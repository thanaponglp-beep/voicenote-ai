# VoiceNote AI — PWA voice recorder + AI summary

อัดเสียงด้วยไมค์ → ส่งให้ Gemini transcribe + สรุป (cloud API, ใช้ได้แม้ PC ปิด)
ไฟล์เสียงเก็บในเครื่องมือถือเท่านั้น (IndexedDB) ไม่ขึ้นเซิร์ฟเวอร์

## ไฟล์
- `index.html` — app ทั้งหมด (หน้าเดียว, dark UI ภาษาไทย)
- `manifest.json` + `sw.js` — PWA install + offline shell
- `serve.py` — local server ให้มือถือเข้าถึงผ่าน LAN
- `register-sw.js` — เปิด service worker อัตโนมัติเมื่อ deploy แบบ HTTPS

## วิธีใช้ (LAN — PC ต้องเปิดอยู่)
1. บน PC:  `python C:\Users\thana\voice-ai-pwa\serve.py`  (port 8140)
2. มือถือต่อ Wi-Fi เครือเดียวกัน → เปิด Chrome ที่ `http://<IP-PC>:8140`
   (IP ดูจากข้อความที่ server พิมพ์, วันนี้คือ 192.168.1.136)
3. **สำคัญ:** mic บน origin ที่ไม่ใช่ localhost ต้องเปิด flag ก่อน:
   - Chrome mobile → `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
     เพิ่ม `http://<IP>:8140` แล้ว Restart
   (หรือ deploy แบบ HTTPS — ดูด้านล่าง — จะไม่ต้องทำขั้นนี้)
4. เปิด app → กด ⚙ ใส่ Gemini API key (ขอฟรีที่ aistudio.google.com → Get API Key)
5. แตะไมค์ → อนุญาต permission → อัด → หยุด → กด "✨ สรุป + Transcribe"

## Deploy ให้ใช้จากที่ไหนก็ได้ (HTTPS, ไม่ต้องเปิด PC, mic ใช้ได้ทันที)
GitHub Pages (เครื่องนี้ยังไม่มี `gh` CLI — ทำใน browser):
1. สร้าง repo ใหม่ที่ github.com (public/private ก็ได้)
2. Upload ไฟล์ทั้ง 5 ไฟล์ของโฟลเดอร์นี้
3. Settings → Pages → Deploy from branch → main → Save
4. เปิด URL `https://<user>.github.io/<repo>/` บนมือถือ
   → menu ⋮ → "Add to Home screen" → icon VoiceNote AI จะขึ้นบนหน้า desktop
   (HTTPS = mic ทำงานทันทีโดยไม่ต้องเปิด flag + service worker เปิดเอง)

## หมายเหตุเทคนิค
- บันทึกเป็น `audio/mp4` (Android Chrome รองรับ) fallback `webm/opus`
- สรุป: `generateContent` inline audio base64, ลอง `gemini-2.5-flash` แล้ว `gemini-3.8-flash` อัตโนมัติ
- ปุ่ม "ทดสอบระบบ" = สร้างเสียง tone 4 โน้ต แล้วอัดกลับ (เดสก์ท็อปจับเสียงระบบ / มือถือใช้ไมค์)
- API key เก็บใน localStorage ของเครื่องนั้นเท่านั้น
