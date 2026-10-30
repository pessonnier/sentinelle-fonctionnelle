(() => {
  "use strict";

  const table = document.querySelector("#product-table");
  if (!table) return;

  const formatMoney = (value) => `${value.toFixed(2)} €`;
  const updateTotals = () => {
    let subtotal = 0;
    table.querySelectorAll("tbody tr").forEach((row) => {
      const price = Number(row.dataset.price || 0);
      const quantity = Number(row.querySelector('input[type="number"]').value || 0);
      const total = price * quantity;
      subtotal += total;
      row.querySelector("[data-line-total]").textContent = formatMoney(total);
    });
    document.querySelector("#live-subtotal").textContent = formatMoney(subtotal);
  };

  table.addEventListener("input", updateTotals);
  updateTotals();
})();
