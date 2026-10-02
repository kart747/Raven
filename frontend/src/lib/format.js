/** ₹ in crore with fixed decimals, e.g. ₹12.40 Cr */
export const formatCrore = (val, digits = 2) => `₹${((val || 0) / 1e7).toFixed(digits)} Cr`;

/** ₹ scaled to Cr / Lakh / rupees depending on size */
export const formatInr = (val) => {
  if (val === undefined || val === null) return '₹0';
  if (val >= 1e7) return `₹${(val / 1e7).toFixed(2)} Cr`;
  if (val >= 1e5) return `₹${(val / 1e5).toFixed(2)} Lakh`;
  return `₹${val.toLocaleString('en-IN')}`;
};

/** FY start year -> "FY2019-20" */
export const fiscalYear = (year) => `FY${year}-${String((year + 1) % 100).padStart(2, '0')}`;
