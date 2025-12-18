// Function to prepare data for Chart.js
function prepareChartData(sightings) {
  const dataPerDay = {};

  // Aggregate data per day and by type
  sightings.forEach(sighting => {
      const date = new Date(sighting.creation_timestamp).toISOString().split('T')[0]; // Extract date (YYYY-MM-DD)
      const type = sighting.type;

      if (!dataPerDay[date]) {
          dataPerDay[date] = {
              "seen": 0,
              "confirmed": 0,
              "published-proof-of-concept": 0,
              "exploited": 0,
              "patched": 0,
              "not-confirmed": 0,
              "not-exploited": 0,
              "not-patched": 0
          };
      }

      if (dataPerDay[date][type] !== undefined) {
          dataPerDay[date][type] += 1; // Increment the count of the specific sighting type for that day
      }
  });

  return dataPerDay;
}

let sightingsChart; // Global variable to hold the chart instance

// Define the color map using shades of green for positive and red for negative values
const colorMap = {
  'seen': 'hsl(19, 95%, 89%)',
  'confirmed': 'hsl(18, 85%, 74%)',
  'published-proof-of-concept': 'hsl(8, 63%, 57%)',
  'exploited': 'hsl(353, 79%, 39%)',

  'patched': 'hsl(205, 52%, 88%)',
  'not-confirmed': 'hsl(202, 56%, 71%)',
  'not-exploited': 'hsl(199, 55%, 50%)',
  'not-patched': 'hsl(208, 83%, 37%)',
};

// Function to draw the Chart using Chart.js
function drawBarChart(sightings) {
  const dataPerDay = prepareChartData(sightings);
  let labels = Object.keys(dataPerDay);

  labels = labels.sort((a, b) => new Date(a) - new Date(b));

  const types = ["seen", "confirmed", "published-proof-of-concept", "exploited", "patched", "not-confirmed", "not-exploited", "not-patched"];

  const datasets = types.map((type) => {
      const isBelowAxis = type.startsWith('not-');
      return {
          label: type,
          backgroundColor: colorMap[type],
          data: labels.map(date => isBelowAxis ? -dataPerDay[date][type] : dataPerDay[date][type]),
          barThickness: 20
      };
  });

  const canvas = document.getElementById("sightingsChart");
  if (!canvas) {
      console.error(`Canvas element with ID "sightingsChart" not found.`);
      return;
  }

  // Destroy the existing chart if it exists
  if (chartInstances["sightingsChart"]) {
      chartInstances["sightingsChart"].destroy();
  }

  const ctx = document.getElementById('sightingsChart').getContext('2d');

  chartInstances["sightingsChart"] = new Chart(ctx, {
      type: 'bar',
      data: {
          labels: labels,
          datasets: datasets
      },
      options: {
          maintainAspectRatio: false,
          onClick: (event, activeElements) => {
              if (activeElements.length > 0) {
                  const elementIndex = activeElements[0].index;
                  const datasetIndex = activeElements[0].datasetIndex;

                  const clickedDate = labels[elementIndex]; // The X-axis label
                  const clickedType = types[datasetIndex]; // The Type (dataset label)

                  filterTableByDateAndType(clickedDate, clickedType, sightings);
                  document.getElementById('reset-table').style.display = 'block';
              }
          },
          scales: {
              x: { stacked: false, beginAtZero: true },
              y: {
                  stacked: false,
                  beginAtZero: true,
                  ticks: {
                      stepSize: 1,
                      callback: (value) => Math.round(Math.abs(value))
                  }
              }
          },
          plugins: {
              legend: { display: true, position: 'top', title: { text: 'Type of sightings', display: true } },
              tooltip: {
                  callbacks: {
                      label: (tooltipItem) => `${tooltipItem.dataset.label}: ${Math.abs(tooltipItem.raw)}`
                  }
              }
          }
      }
  });
}

// Helper to filter the table by date and type
function filterTableByDateAndType(dateString, type, originalData) {
    const DateTime = luxon.DateTime;

    const filtered = originalData.filter(s => {
        const sDate = DateTime.fromISO(s.creation_timestamp).toISODate();
        return sDate === dateString && s.type === type;
    });

    renderTable(filtered);

    // Update the reset button text to be more descriptive
    const resetBtn = document.getElementById('reset-table');
    resetBtn.textContent = `Clear Filter: ${dateString} (${type})`;
    resetBtn.style.display = 'block';
}

// Helper to filter the table by date
function filterTableByDate(dateString, originalData) {
    const filtered = originalData.filter(s =>
        luxon.DateTime.fromISO(s.creation_timestamp).toISODate() === dateString
    );

    renderTable(filtered);

    // Update the reset button text to be more descriptive
    const resetBtn = document.getElementById('reset-table');
    resetBtn.textContent = `Clear Filter: ${dateString}`;
    resetBtn.style.display = 'block';
}


let cal; // Global variable to store the heatmap instance

function drawHeatmap(sightings, originalData) {
    const DateTime = luxon.DateTime;

    // Define priority (highest index = most "severe" color)
    const priorityOrder = [
        'seen', 'confirmed', 'published-proof-of-concept', 'exploited',
        'patched', 'not-confirmed', 'not-exploited', 'not-patched'
    ];

    // 1. Prepare Data: Find the "heaviest" status per day
    const dayStatus = {};
    const dayCounts = {}; // Keep counts for the tooltip

    sightings.forEach(s => {
        const date = DateTime.fromISO(s.creation_timestamp).toISODate();
        dayCounts[date] = (dayCounts[date] || 0) + 1;

        const currentType = s.type;
        const existingType = dayStatus[date];

        if (!existingType || priorityOrder.indexOf(currentType) > priorityOrder.indexOf(existingType)) {
            dayStatus[date] = currentType;
        }
    });

    const heatmapData = Object.keys(dayStatus).map(date => ({
        date: date,
        value: priorityOrder.indexOf(dayStatus[date]), // Use index as the value for the color scale
        count: dayCounts[date] // Pass actual count for tooltip
    }));


    const canvas = document.getElementById("cal-heatmap");
    if (!canvas) {
        console.error(`Canvas element with ID "cal-heatmap" not found.`);
        return;
    }

    // Destroy the existing chart if it exists
    if (chartInstances["cal-heatmap"]) {
        chartInstances["cal-heatmap"].destroy();
    }

    // 2. Initialize CalHeatmap
    cal = new CalHeatmap();
    cal.paint({
        itemSelector: "#cal-heatmap",
        domain: { type: 'month', gutter: 8 },
        subDomain: { type: 'day', radius: 2, width: 15, height: 15, gutter: 4 },
        data: { source: heatmapData, x: 'date', y: 'value' },
        date: { start: DateTime.now().minus({ months: 11 }).toJSDate() },
        scale: {
            color: {
                type: 'ordinal', // Use ordinal to map specific indices to specific colors
                domain: priorityOrder.map((_, i) => i),
                range: priorityOrder.map(type => colorMap[type]),
                // Default color for days with no sightings
                interpolate: (t) => '#e1e4e8'
            },
        },
    },
    [
        [
            typeof Tooltip !== 'undefined' ? Tooltip : CalHeatmapTooltip,
            {
                text: (date, value, dayjsDate) => {
                    // Find the data object for this date to get the true count
                    const dateStr = dayjsDate.format('YYYY-MM-DD');
                    const count = dayCounts[dateStr] || 0;
                    const status = dayStatus[dateStr] || 'none';
                    return `${count} sightings (Max: ${status}) on ${dayjsDate.format('LL')}`;
                }
            }
        ]
    ]);

    // 3. Handle Click Event
    cal.on('click', (event, timestamp, value) => {
        // value is now the priority index, so we check if it's 0 or higher
        if (value === null || value === undefined) return;

        document.getElementById('reset-table').style.display = 'block';

        const clickedDate = DateTime.fromMillis(timestamp).toISODate();
        filterTableByDate(clickedDate, originalData);
        document.getElementById('reset-table').style.display = 'block';
    });

    // Store the instance in order to delete it later
    chartInstances["cal-heatmap"] = cal;
}




async function getVulnVendorProduct(vulnerability_id) {
  try {
    const response = await fetch("/api/vulnerability/" + encodeURIComponent(vulnerability_id));
    const result = await response.json();
    const affected = result?.containers?.cna?.affected;

    if (affected && affected.length > 0) {
      const vendor = affected[0].vendor;
      const product = affected[0].product;
      return `${vendor} / ${product}`;
    } else {
      return "";
    }
  } catch (error) {
    console.error("Error fetching vulnerability data:", error);
    return "";
  }
}


let chartInstances = {}; // Store chart instances by canvas ID
let lastHoveredIndex = null;
const vendorProductCache = {}; // vulnId -> vendor/product

function drawBarChartHomePage(sightings, chartDivId, title, backgroundColor) {
    if (!sightings || sightings.length === 0) {
        console.error("No data provided for the chart.");
        return;
    }

    const vulnerabilityCounts = new Map();

    // Count occurrences of vulnerabilities
    for (const sighting of sightings) {
        const vuln = sighting.vulnerability.toLowerCase();
        vulnerabilityCounts.set(vuln, (vulnerabilityCounts.get(vuln) || 0) + 1);
    }

    // Get top 8 vulnerabilities
    const sortedVulns = Array.from(vulnerabilityCounts.entries())
        .sort(([, a], [, b]) => b - a)
        .slice(0, 8);

    const labels = sortedVulns.map(([vuln]) => vuln);
    const dataCounts = sortedVulns.map(([, count]) => count);

    const canvas = document.getElementById(chartDivId);
    if (!canvas) {
        console.error(`Canvas element with ID "${chartDivId}" not found.`);
        return;
    }

    const parentContainer = canvas.parentElement;
    const height = canvas.style.height || canvas.getAttribute('height'); // Save height before destroying

    // Destroy the existing chart if it exists
    if (chartInstances[chartDivId]) {
        chartInstances[chartDivId].destroy();
    }

    // Remove and recreate the canvas to clean up properly
    parentContainer.innerHTML = `<canvas id="${chartDivId}" height="${height}"></canvas>`;
    const newCanvas = document.getElementById(chartDivId);
    const ctx = newCanvas.getContext('2d');

    // Create a new chart instance and store it
    chartInstances[chartDivId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: title,
                data: dataCounts,
                backgroundColor: Array.isArray(backgroundColor) ? backgroundColor : [backgroundColor],
                borderColor: 'white',
                borderWidth: 1,
            }],
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: false,
                        text: 'Vulnerabilities',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: 'Sightings',
                    },
                    ticks: {
                        stepSize: 1,
                    },
                },
            },
            plugins: {
              tooltip: {
                  callbacks: {
                      label: function(context) {
                          const vulnId = context.label;
                          const vendorProduct = vendorProductCache[vulnId];
                          const count = context.formattedValue;

                          if (vendorProduct) {
                              return `${vendorProduct}: ${count}`;
                          }
                          return `${vulnId}: ${count}`;
                      }
                  }
              }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const vulnId = labels[index];
                    window.location.href = `/vuln/${vulnId}`;
                }
            },
            onHover: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const vulnId = labels[index];

                    if (index !== lastHoveredIndex) {
                        lastHoveredIndex = index;

                        if (!vendorProductCache[vulnId]) {
                            getVulnVendorProduct(vulnId).then((vendorProduct) => {
                              vendorProductCache[vulnId] = vendorProduct;
                            });
                        }
                    }
                } else {
                    lastHoveredIndex = null;
                }
            },
        },
    });
}

function drawVulnerabilityTable(sightings, minSightings, containerId) {
  const container = document.getElementById(containerId);

  // Remove any existing table
  container.innerHTML = '';

  // Process data into a structured format
  const processedData = {};
  const vulnerabilities = new Map(); // Map to store total sightings for sorting

  // Parse and normalize date range based on the sightings
  const allDates = [];

  // Get the earliest and latest dates from sightings and normalize to UTC
  const parsedDates = sightings.map(entry => new Date(entry.creation_timestamp));
  const minDate = new Date(Date.UTC(new Date(Math.min(...parsedDates)).getUTCFullYear(), new Date(Math.min(...parsedDates)).getUTCMonth(), new Date(Math.min(...parsedDates)).getUTCDate()));
  const maxDate = new Date(Date.UTC(new Date(Math.max(...parsedDates)).getUTCFullYear(), new Date(Math.max(...parsedDates)).getUTCMonth(), new Date(Math.max(...parsedDates)).getUTCDate()));

  // Create a full range of dates from minDate to maxDate
  let currentDate = new Date(minDate);
  while (currentDate <= maxDate) {
      allDates.push({
          day: currentDate.getUTCDate(),
          month: currentDate.toLocaleString('default', { month: 'short', timeZone: 'UTC' }),
          fullDate: `${currentDate.getUTCFullYear()}-${String(currentDate.getUTCMonth() + 1).padStart(2, '0')}-${String(currentDate.getUTCDate()).padStart(2, '0')}`, // Format: YYYY-MM-DD
          formattedDate: `${currentDate.toLocaleString('default', { month: 'short', timeZone: 'UTC' })} ${currentDate.getUTCDate()}, ${currentDate.getUTCFullYear()}`, // Format: MM DD, YYYY
      });
      currentDate.setUTCDate(currentDate.getUTCDate() + 1);
  }

  // Calculate maximum count for gradient scaling
  let maxCount = 0;

  sightings.forEach(entry => {
      const date = new Date(entry.creation_timestamp);
      const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      const vuln = entry.vulnerability.toUpperCase(); // Normalize vulnerability ID to uppercase

      if (!processedData[vuln]) {
          processedData[vuln] = {};
          vulnerabilities.set(vuln, 0); // Initialize total sightings count
      }

      if (!processedData[vuln][dateKey]) processedData[vuln][dateKey] = 0;

      processedData[vuln][dateKey]++;
      vulnerabilities.set(vuln, vulnerabilities.get(vuln) + 1); // Increment total sightings count
      maxCount = Math.max(maxCount, processedData[vuln][dateKey]);
  });

  // Sort vulnerabilities by total sightings in descending order
  const vulnerabilitiesArray = Array.from(vulnerabilities.entries())
      .filter(entry => entry[1] >= minSightings) // Filter out lines with less than minSightings
      .sort((a, b) => b[1] - a[1]) // Sort by total sightings
      .map(entry => entry[0]); // Extract sorted vulnerability IDs

  // Create table element
  const table = document.createElement('table');
  table.className = 'table table-bordered table-hover table-sm'; // Bootstrap classes for styling

  // Add caption
  // const caption = document.createElement('caption');
  // caption.className = 'caption-top'; // Bootstrap class for placing caption above the table
  // caption.textContent = 'Evolution for the selected time frame';
  // table.appendChild(caption);

  // Create table header
  const thead = document.createElement('thead');
  thead.className = 'table-light'; // Bootstrap light header background
  const headerRow = document.createElement('tr');

  // Add the first empty header cell for the vulnerability column
  const emptyHeader = document.createElement('th');
  emptyHeader.textContent = '';
  headerRow.appendChild(emptyHeader);

  // Add day headers based on the full range of dates
  allDates.forEach(date => {
      const dayHeader = document.createElement('th');
      dayHeader.textContent = `${date.day}`;
      dayHeader.title = `${date.formattedDate}`;
      dayHeader.style.textAlign = 'center'; // Center the day headers
      headerRow.appendChild(dayHeader);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Create table body
  const tbody = document.createElement('tbody');

  vulnerabilitiesArray.forEach(vuln => {
      const row = document.createElement('tr');

      // Add vulnerability ID as the first column
      const vulnCell = document.createElement('td');
      vulnCell.classList.add('vuln-id-row', 'truncate-cell-sighting-table');
      const vulnLink = document.createElement('a');
      vulnLink.href = `/vuln/${vuln}`;
      vulnLink.textContent = vuln; // Already in uppercase
      vulnLink.style.textDecoration = 'none'; // Optional: Remove underline
      vulnCell.appendChild(vulnLink);
      row.appendChild(vulnCell);

      // Add day cells for all dates
      allDates.forEach(date => {
          const dayCell = document.createElement('td');
          dayCell.style.textAlign = 'center'; // Center the text in the day cells

          const dateKey = date.fullDate; // Match the date key
          if (processedData[vuln] && processedData[vuln][dateKey]) {
              const count = processedData[vuln][dateKey];
              dayCell.textContent = count;

              // Calculate color intensity based on the count
              const intensity = Math.round((count / maxCount) * 255); // Scale to 0–255
              dayCell.style.backgroundColor = `rgba(0, 0, 255, ${0.2 + 0.8 * (intensity / 255)})`; // Blue gradient
              dayCell.style.color = 'white';
              dayCell.style.cursor = 'pointer';

              dayCell.onclick = () => {
                  window.location.href = `/vuln/${vuln}#sightings`;
              };
          } else {
              dayCell.textContent = ''; // Empty cell for missing data
          }

          row.appendChild(dayCell);
      });

      tbody.appendChild(row);
  });

  table.appendChild(tbody);
  container.appendChild(table);
}


function setupVulnIdRowTooltips() {
  const vulnRows = document.querySelectorAll('.vuln-id-row');

  vulnRows.forEach(cell => {
    let tooltipInstance = null;
    let hideTimeout = null;

    cell.addEventListener('mouseenter', async () => {
      if (tooltipInstance) return;

      const link = cell.querySelector('a');
      if (!link) return;

      const vulnId = link.textContent.trim();
      let vendorProduct;

      try {
        vendorProduct = await getVulnVendorProduct(vulnId);
      } catch (e) {
        console.warn("Vendor/product fetch error", e);
        vendorProduct = null;
      }

      const tooltipText = (vendorProduct && vendorProduct !== "n/a / n/a")
        ? vendorProduct
        : 'No vendor/product info available';

      // Remove any old title to avoid conflict
      cell.removeAttribute('title');
      cell.setAttribute('data-bs-title', tooltipText);

      // Create and store tooltip
      tooltipInstance = bootstrap.Tooltip.getInstance(cell) || new bootstrap.Tooltip(cell, {
        trigger: 'manual',
        placement: 'top'
      });
      tooltipInstance.show();

      // Auto-hide after 2.5s
      hideTimeout = setTimeout(() => {
        if (tooltipInstance) {
          tooltipInstance.hide();
          tooltipInstance.dispose();
          tooltipInstance = null;
        }
      }, 2500);
    });

    cell.addEventListener('mouseleave', () => {
      if (hideTimeout) {
        clearTimeout(hideTimeout);
        hideTimeout = null;
      }

      if (tooltipInstance) {
        tooltipInstance.hide();
        tooltipInstance.dispose();
        tooltipInstance = null;
      }
    });
  });
}
