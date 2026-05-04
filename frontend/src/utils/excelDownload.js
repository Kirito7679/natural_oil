/**
 * Excel download helper — downloads .xlsx file via authenticated request.
 */
export async function downloadExcel(endpoint, params = {}, filename = 'export.xlsx') {
    const token = localStorage.getItem('token');
    const url = new URL(`http://localhost:8000/api/export/${endpoint}`);

    Object.entries(params).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '') {
            url.searchParams.append(k, v);
        }
    });

    try {
        const res = await fetch(url.toString(), {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
            alert("Excel yuklab bo'lmadi.");
            return;
        }

        const blob = await res.blob();
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objUrl);
    } catch (e) {
        console.error(e);
        alert("Excel yuklab bo'lmadi.");
    }
}