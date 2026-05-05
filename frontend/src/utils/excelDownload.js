/**
 * Excel download helper — downloads .xlsx file via authenticated request.
 */
import client from '../api/client';

export async function downloadExcel(endpoint, params = {}, filename = 'export.xlsx') {
    try {
        const res = await client.get(`/export/${endpoint}`, {
            params,
            responseType: 'blob'
        });

        const blob = new Blob([res.data]);
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