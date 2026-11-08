/**
 * Telefonda jadvallar kartochka ko'rinishida chiqadi.
 * Buning uchun har bir katakka (td) ustun nomi data-label sifatida yoziladi.
 * Bitta kuzatuvchi butun ilova uchun ishlaydi — sahifalarni o'zgartirish shart emas.
 */
function labelTables() {
  document.querySelectorAll('table.data-table').forEach((table) => {
    const heads = Array.from(table.querySelectorAll('thead th')).map((th) => th.textContent.trim());
    if (!heads.length) return;
    table.querySelectorAll('tbody tr, tfoot tr').forEach((tr) => {
      Array.from(tr.children).forEach((td, i) => {
        const label = heads[i] || '';
        if (td.getAttribute('data-label') !== label) td.setAttribute('data-label', label);
      });
    });
  });
}

export function startTableLabels() {
  let scheduled = false;
  const run = () => {
    scheduled = false;
    labelTables();
  };
  const observer = new MutationObserver(() => {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(run);
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
  labelTables();
}
