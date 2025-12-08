#!/usr/bin/env python3
import os
from uuid import UUID

from flask import (
    Blueprint,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (  # type: ignore[import-untyped]
    current_user,
    login_required,
)
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
)
from markupsafe import Markup, escape
from sqlalchemy import or_
from werkzeug import Response as WerkzeugResponse

from website.lib.utils import escape_ilike
from website.models import (
    CPEProduct,
    Icon,
    Language,
    License,
    Organization,
    Product,
)
from website.web.bootstrap import application, db
from website.web.forms import (
    ProductCPEProductForm,
    ProductForm,
)
from website.web.permissions import admin_permission

admin_product_bp = Blueprint("admin_product_bp", __name__, url_prefix="/admin/product")
admin_products_bp = Blueprint(
    "admin_products_bp", __name__, url_prefix="/admin/products"
)


@admin_products_bp.route("/", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def list_products() -> str:
    product_query = request.args.get("query", "")
    products = Product.query
    if product_query:
        escaped_query = escape_ilike(product_query)
        try:
            uuid_obj = UUID(product_query)
        except Exception:
            uuid_obj = None
        if uuid_obj:
            products = products.filter(
                or_(
                    Product.uuid == uuid_obj,
                    Product.name.ilike(f"%{escaped_query}%", escape="\\"),
                    Product.organizations.any(
                        Organization.name.ilike(f"%{escaped_query}%", escape="\\")
                    ),
                    Product.organizations.any(
                        Organization.short_name.ilike(f"%{escaped_query}%", escape="\\")
                    ),
                )
            )
        else:
            products = products.filter(
                or_(
                    Product.name.ilike(f"%{escaped_query}%", escape="\\"),
                    Product.organizations.any(
                        Organization.name.ilike(f"%{escaped_query}%", escape="\\")
                    ),
                    Product.organizations.any(
                        Organization.short_name.ilike(f"%{escaped_query}%", escape="\\")
                    ),
                )
            )
    products = products.order_by(Product.creation_timestamp.desc())
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=products.count(),
        record_name="products",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    products = products.offset(offset).limit(per_page)

    return render_template(
        "admin/products.html",
        products=products,
        pagination=pagination,
    )


@admin_product_bp.route("/create", methods=["GET"])
@admin_product_bp.route("/edit/<int:product_id>", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def form_product(product_id: int = 0) -> str:
    """Return a form to create and edit a product."""
    action = "Add a product"
    head_titles = [action]
    form = ProductForm()
    if not product_id:
        return render_template(
            "admin/edit_product.html",
            action=action,
            head_titles=head_titles,
            form=form,
        )

    product = Product.query.filter(Product.id == product_id).first()
    form = ProductForm(obj=product)
    form.organizations.data = [
        organization.id for organization in product.organizations
    ]
    form.licenses.data = [license.id for license in product.licenses]
    form.languages.data = [language.id for language in product.languages]
    action = "Edit a product"
    head_titles = [action]
    head_titles.append(product.name)
    return render_template(
        "admin/edit_product.html",
        action=action,
        head_titles=head_titles,
        form=form,
        product=product,
    )


@admin_product_bp.route("/create", methods=["POST"])
@admin_product_bp.route("/edit/<int:product_id>", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def process_product_form(product_id: int = 0) -> str | WerkzeugResponse:
    """Edit a product."""
    form = ProductForm()

    if not form.validate():
        return render_template("admin/edit_product.html", form=form)

    # Edit an existing product
    if product_id:
        product = Product.query.filter(Product.id == product_id).first()

        # Logo
        f = form.logo.data
        if f:
            try:
                # Delete the previous icon
                old_icon = Icon.query.filter(Icon.id == product.icon_id).first()
                icon_url = os.path.join(
                    application.config["UPLOAD_FOLDER"], old_icon.url
                )
                os.unlink(icon_url)
                db.session.delete(old_icon)
                product.icon_id = None
                db.session.commit()
            except Exception as e:
                print(e)

            # Save the new icon
            filename = f"{product.uuid}.png"
            icon_url = os.path.join(application.config["UPLOAD_FOLDER"], filename)
            f.save(icon_url)
            # Create the corresponding new icon object
            new_icon = Icon(url=filename)
            db.session.add(new_icon)
            db.session.commit()
            product.icon_id = new_icon.id

        # Organizations
        new_organizations = []
        for organization_id in form.organizations.data:
            organization = Organization.query.filter(
                Organization.id == organization_id
            ).first()
            if not organization:
                continue
            new_organizations.append(organization)
        product.organizations = new_organizations
        del form.organizations

        # Licenses
        new_licenses = []
        for license_id in form.licenses.data:
            license = License.query.filter(License.id == license_id).first()
            new_licenses.append(license)
        product.licenses = new_licenses
        del form.licenses

        # Languages
        new_languages = []
        for language_id in form.languages.data:
            language = Language.query.filter(Language.id == language_id).first()
            new_languages.append(language)
        product.languages = new_languages
        del form.languages

        form.populate_obj(product)
        db.session.commit()
        flash(f"Product {form.name.data} successfully updated.", "success")
        return redirect(
            url_for(
                "admin_product_bp.form_product",
                product_id=product.id,
            )
        )

    # Create a new product
    new_product = Product(
        name=form.name.data,
        short_name=form.short_name.data,
        description=form.description.data,
        short_description=form.short_description.data,
        website=form.website.data,
        submitter_id=current_user.id,
    )
    # Organizations
    for organization_id in form.organizations.data:
        organization = Organization.query.filter(
            Organization.id == organization_id
        ).first()
        if not organization:
            continue
        new_product.organizations.append(organization)
    # Licenses
    for license_id in form.licenses.data:
        license = License.query.filter(License.id == license_id).first()
        new_product.licenses.append(license)
    del form.licenses
    # Languages
    for language_id in form.languages.data:
        language = Language.query.filter(Language.id == language_id).first()
        new_product.languages.append(language)
    del form.languages

    db.session.add(new_product)
    db.session.commit()

    # Icon
    f = form.logo.data
    if f:
        filename = f"{new_product.uuid}.png"
        icon_url = os.path.join(application.config["UPLOAD_FOLDER"], filename)
        f.save(icon_url)
        # Create the corresponding new icon object
        new_icon = Icon(url=filename)
        db.session.add(new_icon)
        db.session.commit()
        new_product.icon_id = new_icon.id

    flash(
        f"Product {new_product.name} successfully created.",
        "success",
    )
    return redirect(
        url_for(
            "admin_product_bp.form_product",
            product_id=new_product.id,
        )
    )


@admin_product_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def delete_product(product_id: int = 0) -> WerkzeugResponse:
    """Allow administrators to delete a product."""
    product = Product.query.filter(Product.id == product_id).first()
    if product is None:
        abort(404)
    CPEProduct.query.filter(CPEProduct.product_id == product.id).delete()
    db.session.commit()
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("admin_products_bp.list_products"))


@admin_product_bp.route("/<int:product_id>/cpe_product", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def form_product_cpe_product(product_id: int) -> str:
    product = Product.query.filter(Product.id == product_id).first()
    if not product:
        abort(404)

    form = ProductCPEProductForm()

    action = f"Manage CPE product names for {product.name}"
    head_titles = [action]

    return render_template(
        "admin/edit_product_cpe_product.html",
        action=action,
        head_titles=head_titles,
        form=form,
        product=product,
    )


@admin_product_bp.route("/<int:product_id>/cpe_product", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def process_form_product_cpe_product(
    product_id: int,
) -> str | WerkzeugResponse:
    product = Product.query.filter(Product.id == product_id).first()
    if not product:
        abort(404)

    form = ProductCPEProductForm()

    if not form.validate():
        return render_template("admin/edit_product_cpe_product.html", form=form)

    if cpe_product := CPEProduct.query.filter(
        CPEProduct.name == form.name.data
    ).first():
        url = url_for(
            "admin_product_bp.form_product_cpe_product",
            product_id=cpe_product.product_id,
        )

        flash(
            Markup(
                f"CPE Product Name already defined for "
                f"<a href='{escape(url)}'>{escape(cpe_product.product.name)}</a>."
            ),
            "danger",
        )

        return redirect(
            url_for(
                "admin_product_bp.form_product_cpe_product",
                product_id=product_id,
            )
        )

    try:
        new_product_name = CPEProduct(name=form.name.data, product_id=product_id)

        db.session.add(new_product_name)
        db.session.commit()

        flash("CPE product name created.", "success")
    except ValueError:
        flash("Invalid name.", "danger")

    return redirect(
        url_for(
            "admin_product_bp.form_product_cpe_product",
            product_id=product_id,
        )
    )


@admin_product_bp.route(
    "/<int:product_id>/cpe_product/<int:cpe_product_name_id>/delete",
    methods=["POST"],
)
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def delete_cpe_product(product_id: int, cpe_product_name_id: int) -> WerkzeugResponse:
    """Allow administrators to delete a CPE product name."""
    product = Product.query.filter(Product.id == product_id).first()
    if product is None:
        abort(404)
    cpe_product_name = CPEProduct.query.filter(
        CPEProduct.id == cpe_product_name_id
    ).first()
    if cpe_product_name is None:
        abort(404)
    db.session.delete(cpe_product_name)
    db.session.commit()
    flash("CPE product name deleted.", "success")
    return redirect(
        url_for(
            "admin_product_bp.form_product_cpe_product",
            product_id=product_id,
        )
    )


@admin_product_bp.route(
    "/<uuid:product_uuid>/export_cpe_information",
    methods=["GET"],
)
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def export_cpe_information(product_uuid: str) -> WerkzeugResponse:
    """Export CPE information for the product."""
    product = Product.query.filter(Product.uuid == product_uuid).first()
    if product is None:
        abort(404)

    # Create a response with the raw JSON data
    response = make_response(product.as_json())

    # Set headers for file download and proper content type
    response.headers["Content-Disposition"] = (
        f"attachment; filename={product.uuid}.json"
    )
    response.headers["Content-Type"] = "application/json"

    return response
