const API = () => window.API_BASE;
export const post = (url, body) => fetch(API()+url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) }).then(r=>r.json());
export const get  = (url) => fetch(API()+url).then(r=>r.json());
