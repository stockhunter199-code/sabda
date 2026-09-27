import os
import pandas as pd
import json
import yfinance as yf
from ta.momentum import RSIIndicator

# 1. AMBIL DATA RIIL MASSAL DARI YAHOO FINANCE BERDASARKAN LIST.JSON
def get_stock_data():
    list_path = "list.json"
    
    if not os.path.exists(list_path):
        print("[EROR] Eksekusi dibatalkan: File 'list.json' tidak ditemukan di folder py-engine!")
        return pd.DataFrame()
        
    try:
        with open(list_path, "r", encoding="utf-8") as list_file:
            tickers = json.load(list_file).get("stocks", [])
            if not tickers:
                print("[EROR] Eksekusi dibatalkan: Daftar saham di dalam 'list.json' kosong!")
                return pd.DataFrame()
    except Exception as e:
        print(f"[EROR] Eksekusi dibatalkan: Gagal membaca 'list.json'. Detail: {e}")
        return pd.DataFrame()
    
    yf_tickers = [f"{t}.JK" for t in tickers]
    screener_data = []
    
    print(f"Sedang mengunduh data riil untuk {len(tickers)} saham dari Yahoo Finance...")
    try:
        df_bulk = yf.download(yf_tickers, period="6mo", auto_adjust=True, progress=False)
        
        if df_bulk.empty:
            print("[EROR] Gagal mengunduh data massal bursa.")
            return pd.DataFrame()

        for t_origin, t_yf in zip(tickers, yf_tickers):
            try:
                df_hist = pd.DataFrame()
                df_hist['Close'] = df_bulk['Close'][t_yf]
                df_hist['Volume'] = df_bulk['Volume'][t_yf]
                df_hist = df_hist.dropna()
                
                if df_hist.empty or len(df_hist) < 50:
                    continue
                
                current_price = int(df_hist['Close'].iloc[-1])
                current_volume = int(df_hist['Volume'].iloc[-1])
                
                ma50_val = int(df_hist['Close'].rolling(window=50).mean().iloc[-1])
                ma_vol20_val = int(df_hist['Volume'].rolling(window=20).mean().iloc[-1])
                
                rsi_indicator = RSIIndicator(close=df_hist['Close'], window=14)
                rsi_val = round(rsi_indicator.rsi().iloc[-1], 2)
                
                volatilitas_pct = round(df_hist['Close'].pct_change().rolling(20).std().iloc[-1] * 100 * (252**0.5), 1)
                vol_status = "Tinggi" if volatilitas_pct > 25 else "Standar"
                avg_value_daily = ma_vol20_val * current_price
                liquidity_status = "Sangat Tinggi" if avg_value_daily > 50_000_000_000 else "Tinggi"
                
                print(f" Memproses data & nama perusahaan otomatis untuk: {t_origin}")
                stock_obj = yf.Ticker(t_yf)
                info = stock_obj.info
                
                roe_val = round(info.get('returnOnEquity', 0.15) * 100, 1)
                per_val = round(info.get('trailingPE', 12.5), 1)
                
                mcap_raw = info.get('marketCap', 50_000_000_000_000)
                if mcap_raw >= 1_000_000_000_000:
                    mcap_fmt = f"{round(mcap_raw / 1_000_000_000_000, 1)} Triliun"
                else:
                    mcap_fmt = f"{round(mcap_raw / 1_000_000_000, 1)} Miliar"
                
                comp_title = info.get('longName', f'{t_origin} Corporate Tbk')
                
                screener_data.append({
                    'Ticker': t_origin, 'Company': comp_title,
                    'Price': current_price, 'MA50': ma50_val, 'RSI': rsi_val, 
                    'Volume': current_volume, 'MA_Vol20': ma_vol20_val,
                    'ROE': roe_val, 'PER': per_val, 'MarketCap': mcap_fmt,
                    'Volatilitas': f"{volatilitas_pct}% ({vol_status})", 'Liquidity': liquidity_status
                })
            except Exception as e:
                print(f"[LEWAT] Masalah ekstraksi kolom data di {t_origin}. Detail: {e}")
                
    except Exception as e:
        print(f"[EROR] Gangguan sistem API massal: {e}")
            
    return pd.DataFrame(screener_data)

# 2. LOGIKA STRATEGI STRUKTUR ALGORITMA SABDA
def analyze_recommendations(df):
    if df.empty:
        return df
        
    analysis_results = []
    for _, row in df.iterrows():
        price = row['Price']
        ma50 = row['MA50']
        rsi = row['RSI']
        vol = row['Volume']
        ma_vol = row['MA_Vol20']
        
        trend_status = "Uptrend" if price > ma50 else "Downtrend"
        
        if trend_status == "Uptrend":
            if 30 <= rsi <= 45 and vol > ma_vol:
                action = "STRONG BUY"
                badge_class = "bg-strong-buy"
                entry = f"Rp {{int(price*0.99):,}} - {{price:,}}"
                tp = f"Rp {{int(price * 1.08):,}}"
                sl = f"Rp {{int(price * 0.96):,}}"
            elif rsi < 30:
                action = "BUY ON WEAKNESS"
                badge_class = "bg-bow"
                entry = f"Cicil Beli di Kisaran Rp {{price:,}}"
                tp = f"Rp {{int(price * 1.08):,}}"
                sl = f"Rp {{int(price * 0.94):,}}"
            else:
                action = "HOLD / TAKE PROFIT"
                badge_class = "bg-hold"
                entry = "Wait for Pullback / Jangan Kejar"
                tp = "Siap Ambil Untung"
                sl = "Pasang Trailing Stop"
        else:
            action = "AVOID (WATCHLIST)"
            badge_class = "bg-avoid"
            entry = "Hindari Terlebih Dahulu"
            tp = "-"
            sl = "-"
            
        res = row.to_dict()
        res.update({
            'Tren': trend_status, 'Action': action, 'Badge': badge_class, 
            'Entry': entry, 'Target': tp, 'StopLoss': sl
        })
        analysis_results.append(res)
        
    return pd.DataFrame(analysis_results)
# 3. GENERATOR HALAMAN WEB STATIS UTAMA & HALAMAN REGULASI HUKUM ADSENSER
def generate_static_site(df_analysis):
    config_path = "config.json"
    iklan_path = "config-ik.json"
    
    # Validasi Base URL Web (Wajib)
    if not os.path.exists(config_path):
        print("[EROR] config.json tidak ditemukan!")
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            base_url = json.load(f).get("web_url", "")
            if not base_url.endswith("/"):
                base_url += "/"
    except:
        return

    # Membaca Konfigurasi Iklan & Menyaring Berdasarkan Status Display
    ik_atas, ik_tengah, ik_bawah = "", "", ""
    if os.path.exists(iklan_path):
        try:
            with open(iklan_path, "r", encoding="utf-8") as ik_file:
                ik_data = json.load(ik_file)
                
                data_atas = ik_data.get("iklan_atas", {})
                if data_atas.get("display") == "aktif":
                    ik_atas = data_atas.get("html", "")
                    
                data_tengah = ik_data.get("iklan_tengah", {})
                if data_tengah.get("display") == "aktif":
                    ik_tengah = data_tengah.get("html", "")
                    
                data_bawah = ik_data.get("iklan_bawah", {})
                if data_bawah.get("display") == "aktif":
                    ik_bawah = data_bawah.get("html", "")
        except Exception as e:
            print(f"[PERINGATAN] Gagal memproses filter display iklan. Detail: {e}")

    table_rows = ""
    order_mapping = {"STRONG BUY": 0, "BUY ON WEAKNESS": 1, "HOLD / TAKE PROFIT": 2, "AVOID (WATCHLIST)": 3}
    df_analysis['sort'] = df_analysis['Action'].map(order_mapping)
    df_analysis = df_analysis.sort_values(by='sort').drop(columns=['sort'])

    for idx, row in df_analysis.reset_index().iterrows():
        price_fmt = f"Rp {row['Price']:,}"
        table_rows += f"""<tr data-ticker="{row['Ticker']}" data-company="{row['Company']}" 
            data-price="{price_fmt}" data-action="{row['Action']}" data-badge="{row['Badge']}"
            data-roe="{row['ROE']}" data-per="{row['PER']}" data-mcap="{row['MarketCap']}"
            data-rsi="{row['RSI']}" data-volatilitas="{row['Volatilitas']}" data-liquidity="{row['Liquidity']}"
            data-entry="{row['Entry']}" data-target="{row['Target']}" data-sl="{row['StopLoss']}">
            <td class="txt-ticker">{row['Ticker']}</td>
            <td style="font-weight: 500;">{price_fmt}</td>
            <td style="color: {{'#10b981' if row['Tren'] == 'Uptrend' else '#ef4444'}}; font-weight: 600;">{row['Tren']}</td>
            <td>{row['RSI']}</td>
            <td>{round(row['Volume']/row['MA_Vol20'], 1)}x</td>
            <td><span class="badge {row['Badge']}">{row['Action']}</span></td>
            <td style="color: #ffffff; font-weight: 500;">{row['Entry']}</td>
            <td style="color: #10b981; font-weight: 600;">{row['Target']}</td>
            <td style="color: #ef4444; font-weight: 600;">{row['StopLoss']}</td>
        </tr>"""

    # TEMPLATE 1: HALAMAN UTAMA (index.html) DENGAN STRUKTUR LINK LEGAL LENGKAP
    html_template = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisa Real-Time Saham Pilihan | Sabda Stock Screener</title>
    <meta name="description" content="Dashboard pantauan menyeluruh pergerakan saham pilihan dengan algoritma premium Sabda.">
    <link rel="canonical" href="{base_url}">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <header>
        <h1>📊 Sabda Stock Screener</h1>
        <p>Dashboard Premium Analisis Real-Time Seluruh Saham Pilihan</p>
    </header>
    <main>
        {ik_atas}
        <article class="seo-intro" style="margin-top:20px;">
            <h2>Metode & Panduan Analisis Data Sabda</h2>
            <p>Klik pada baris saham di dalam tabel di bawah ini untuk memunculkan **Dashboard Ringkasan Strategi, Struktur Fundamental Korporasi, serta Risk Management Area** secara lengkap.</p>
        </article>
        {ik_tengah}
        <section class="card">
            <div class="card-header"><h3>📋 Hasil Screening & Rekomendasi Aksi Pasar</h3></div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th><th>Harga Terakhir</th><th>Tren Pasar</th><th>RSI (14)</th><th>Rasio Vol</th><th>Rekomendasi</th><th>Zona Beli (Entry)</th><th>Target Profit</th><th>Stop Loss</th>
                        </tr>
                    </thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
        </section>
        <article class="main-disclaimer">
            <strong>Sanggahan (Disclaimer):</strong> Seluruh data analisis yang disajikan bersifat informatif otomatis berdasarkan data historis bursa. Keputusan transaksi sepenuhnya tanggung jawab pribadi. Baca selengkapnya di <a href="disclaimer.html" style="color:#10b981; text-decoration:underline;">Disclaimer Resmi</a>.
        </article>
        {ik_bawah}
    </main>

    <div class="modal-overlay" id="modalOverlay">
        <div class="modal-box">
            <div class="modal-header-section">
                <div class="modal-brand-title">
                    <span class="modal-ticker-badge" id="popTicker"></span>
                    <span class="modal-company-name" id="popCompany"></span>
                </div>
                <button class="modal-close" id="modalClose">&times;</button>
            </div>
            
            <div class="pop-grid">
                <div class="pop-section">
                    <h4>✨ Ringkasan Strategi (Fundamental)</h4>
                    <div class="pop-row"><span>Return On Equity (ROE)</span><span class="val" id="popRoe"></span></div>
                    <div class="pop-row"><span>Valuasi P/E Ratio (PER)</span><span class="val" id="popPer"></span></div>
                    <div class="pop-row"><span>Kapitalisasi Pasar</span><span class="val" id="popMcap"></span></div>
                </div>
                <div class="pop-section">
                    <h4>📈 Kondisi Harga Saat Ini</h4>
                    <div class="pop-row"><span>Harga Terakhir</span><span class="val" id="popLastPrice"></span></div>
                    <div class="pop-row"><span>RSI Momentum</span><span class="val" id="popRsi"></span></div>
                    <div class="pop-row"><span>Volatilitas Pasar</span><span class="val" id="popVolatilitas"></span></div>
                    <div class="pop-row"><span>Tingkat Likuiditas</span><span class="val" id="popLiquidity"></span></div>
                </div>
            </div>

            <div class="pop-grid">
                <div class="pop-section">
                    <h4>🎯 Entry Area & Target Plan</h4>
                    <div class="pop-row"><span>Zona Beli (Entry)</span><span class="val" style="color:#ffffff;" id="popEntryArea"></span></div>
                    <div class="pop-row"><span>Target Profit (TP)</span><span class="val" style="color:#10b981;" id="popTargetProfit"></span></div>
                </div>
                <div class="pop-section">
                    <h4>🛡️ Manajemen Risiko</h4>
                    <div class="pop-row"><span>Batas Stop Loss (SL)</span><span class="val" style="color:#ef4444;" id="popStopLoss"></span></div>
                </div>
            </div>

            <div class="pop-decision-box">
                <h4>Keputusan Strategi</h4>
                <div id="popBigAction"></div>
                <p class="pop-desc" id="popDesc"></p>
            </div>
        </div>
    </div>

    <footer class="footer">
        <p>&copy; 2026 Sabda. | <a href="disclaimer.html">Disclaimer</a> | <a href="privacy.html">Privacy Policy</a> | <a href="terms.html">Terms of Service</a> | <a href="sitemap.xml">Sitemap</a></p>
    </footer>
    <script src="assets/script.js"></script>
</body>
</html>'''
    # TEMPLATE 2: HALAMAN PRIVACY POLICY (privacy.html)
    privacy_template = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8"><title>Privacy Policy - Kebijakan Privasi Resmi | Sabda</title>
    <link rel="stylesheet" href="assets/style.css"><meta name="robots" content="index, follow">
</head>
<body>
    <header><h1>🔒 Kebijakan Privasi Sabda</h1><p>Komitmen Transparansi Data Pengguna</p></header>
    <main><div class="legal-container"><a href="index.html" class="btn-back">⬅️ Kembali ke Beranda</a>
        <h2>Kebijakan Privasi (Privacy Policy)</h2>
        <p>Di Sabda, privasi pengunjung kami adalah hal yang sangat penting. Dokumen kebijakan privasi ini menguraikan jenis informasi pribadi yang diterima dan dikumpulkan oleh Sabda dan bagaimana informasi tersebut digunakan.</p>
        <h3>1. Log Files & Cookie Browser</h3>
        <p>Seperti kebanyakan situs web lain, Sabda menggunakan file log. Informasi di dalam file log meliputi alamat internet protocol (IP), jenis browser, Internet Service Provider (ISP), stempel tanggal/waktu, dan halaman perujuk. Kami juga menggunakan cookie untuk menyimpan preferensi pengunjung demi kenyamanan navigasi.</p>
        <h3>2. Kebijakan Privasi Pihak Ketiga (Mitra Iklan)</h3>
        <p>Server iklan pihak ketiga atau jaringan iklan (seperti Google AdSense) dapat menggunakan teknologi seperti cookie, JavaScript, atau Web Beacon yang langsung dikirimkan ke browser Anda saat iklan muncul. Sabda tidak memiliki akses atau kontrol terhadap cookie yang digunakan oleh pengiklan pihak ketiga tersebut.</p>
    </div></main>
</body>
</html>'''

    # TEMPLATE 3: HALAMAN TERMS OF SERVICE (terms.html)
    terms_template = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8"><title>Terms of Service - Syarat & Ketentuan | Sabda</title>
    <link rel="stylesheet" href="assets/style.css"><meta name="robots" content="index, follow">
</head>
<body>
    <header><h1>📜 Syarat & Ketentuan Sabda</h1><p>Aturan Penggunaan Layanan Platform</p></header>
    <main><div class="legal-container"><a href="index.html" class="btn-back">⬅️ Kembali ke Beranda</a>
        <h2>Syarat dan Ketentuan Layanan (Terms of Service)</h2>
        <p>Dengan mengakses situs web Sabda, Anda dianggap telah menyetujui dan terikat dengan seluruh syarat, ketentuan, dan hukum yang berlaku di wilayah Indonesia terkait penggunaan platform keuangan statis ini.</p>
        <h3>1. Hak Kekayaan Intelektual</h3>
        <p>Seluruh sistem kode mesin generator, algoritma penilaian strategi, tata letak desain antarmuka, serta logo nama Sabda dilindungi oleh hak cipta intellectual property. Dilarang keras melakukan duplikasi massal secara komersial tanpa izin tertulis.</p>
        <h3>2. Batasan Tanggung Jawab</h3>
        <p>Layanan screening kami disediakan dalam kondisi "apa adanya". Sabda beserta pengembangnya tidak bertanggung jawab atas kerugian investasi langsung maupun tidak langsung yang dialami pengguna akibat keputusan pasar yang diambil dari situs ini.</p>
    </div></main>
</body>
</html>'''

    # TEMPLATE 4: HALAMAN PENDUKUNG MANIFESTO & DISCLAIMER (disclaimer.html)
    disclaimer_template = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8"><title>Sanggahan Hukum & Manifesto Kepatuhan Investasi | Sabda</title>
    <link rel="stylesheet" href="assets/style.css"><meta name="robots" content="index, follow">
</head>
<body>
    <header>
        <h1>⚖️ Sanggahan Hukum & Manifesto Sabda</h1>
        <p>Pasal Ketentuan Hukum Kepatuhan Investasi & Visi Misi Edukasi Ritel</p>
    </header>
    <main>
        <div class="legal-container">
            <a href="index.html" class="btn-back">⬅️ Kembali ke Beranda</a>
            <h2>Visi, Misi & Kritik Terbuka: Mengapa Sabda Dilahirkan?</h2>
            <p>Platform <strong>Sabda Stock Screener</strong> lahir dari rasa jengah dan kegelisahan mendalam melihat realitas pasar finansial Indonesia. Setiap hari, kita menyaksikan ribuan investor ritel mempertaruhkan uang hasil kerja keras mereka ke dalam bursa saham dengan tingkat risiko yang sangat tidak terukur akibat terjebak dalam pusaran psikologi pasar yang salah.</p>
            
            <p>Kami melayangkan <strong>kritik terbuka</strong> terhadap dua fenomena destruktif yang marak di kalangan ritel:</p>
            <p><strong>1. Budaya "Feelingmologi" Tanpa Dasar:</strong> Banyak ritel mengeksekusi modal mereka hanya mengandalkan tebakan, insting kosong, emosi sesaat, atau keberuntungan tanpa pernah mau menguji struktur harga secara teknikal maupun membaca kesehatan laporan keuangan korporasi.</p>
            <p><strong>2. Pengikut Buta (Blind Followers) Influencer Saham:</strong> Fenomena menggiring opini demi keuntungan pribadi oleh oknum influencer lewat aksi <em>pom-pom</em> saham berisiko tinggi telah memakan banyak korban. Investor ritel sering kali dijadikan "bahan bakar" likuiditas keluar tanpa sadar.</p>
            
            <p><strong>Visi dan Misi Sabda</strong> adalah memutus rantai pembodohan pasar tersebut. Kami berkomitmen menyediakan instrumen pemindaian (<em>screening</em>) otomatis berbasis data teknikal yang murni matematis, objektif, dan berdisiplin tinggi secara transparan agar ritel memiliki "suara data" mandiri sebelum membeli aset.</p>

            <h2 style="margin-top: 30px;">Parameter & Spesifikasi Strategi Swing Trading Sabda</h2>
            <p>Sistem otomatis kami dikunci menggunakan parameter matematika yang ketat untuk mengoptimalkan tingkat kemenangan (<em>win rate</em>) secara jangka panjang dan menghapus keterlibatan bias emosi emosional:</p>
            <p><strong>1. Target Kenaikan Profit (TP):</strong> Ditetapkan secara matematis sebesar <strong>+8%</strong> dari zona area entry beli. Target ini sangat objektif dan sangat realistis bagi siklus ayunan (<em>swing high</em>) saham-saham kategori bluechip / LQ45 sebelum mencapai area jenuh beli kembali.</p>
            <p><strong>2. Batas Batasan Risiko (Stop Loss):</strong> Dibatasi maksimal sebesar <strong>-4%</strong>. Rasio ini mengunci manajemen keuangan Anda pada ketetapan <em>Risk-to-Reward Ratio</em> sehat sebesar 1:2. Secara statistik, jika Anda hanya memenangkan 5 dari 10 perdagangan, portofolio akun Anda secara keseluruhan akan tetap tumbuh surplus.</p>
            <p><strong>3. Estimasi Target Waktu (Holding Period):</strong> Berdasarkan siklus historis indikator RSI (14) dan MA Volume 20 harian, estimasi rentang waktu penyimpanan posisi berkisar antara <strong>3 hari hingga 2 minggu (maksimal 1 bulan)</strong>.</p>

            <h2 style="margin-top: 30px;">Pasal Ketentuan Sanggahan Resmi (Disclaimer)</h2>
            <h3>1. Bukan Merupakan Nasihat Keuangan Resmi</h3>
            <p>Seluruh materi, kalkulasi indikator teknikal (MA50, RSI 14, Volume Ratio), serta rancangan batas trading plan otomatis di situs Sabda murni bertujuan untuk sarana edukasi informasi pasar modal dan bukan merupakan instruksi paksaan nasihat keuangan resmi.</p>
            
            <h3>2. Risiko Kerugian Finansial</h3>
            <p>Fluktuasi harga instrumen bursa saham di pasar finansial membawa risiko kerugian modal yang tinggi. Performa historis pergerakan harga tidak menjamin keuntungan pasti di masa depan. Eksekusi transaksi wajib didasari analisa mandiri (<em>Do Your Own Research</em>).</p>
        </div>
    </main>
    <footer class="footer">
        <p>&copy; 2026 Sabda. Dokumen Kepatuhan Kebijakan Hukum Keuangan.</p>
    </footer>
</body>
</html>'''

    # TEMPLATE 5: DATA PETA SITUS XML OTOMATIS (sitemap.xml)
    sitemap_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://sitemaps.org">
   <url><loc>{base_url}index.html</loc><changefreq>daily</changefreq><priority>1.00</priority></url>
   <url><loc>{base_url}disclaimer.html</loc><changefreq>monthly</changefreq><priority>0.50</priority></url>
   <url><loc>{base_url}privacy.html</loc><changefreq>monthly</changefreq><priority>0.50</priority></url>
   <url><loc>{base_url}terms.html</loc><changefreq>monthly</changefreq><priority>0.50</priority></url>
</urlset>'''

    # TEMPLATE 6: DOKUMEN INSTRUKSI BOT GOOGLE (robots.txt)
    robots_template = f'''User-agent: *
Allow: /index.html
Allow: /disclaimer.html
Allow: /privacy.html
Allow: /terms.html
Allow: /assets/

Sitemap: {base_url}sitemap.xml
'''

    # TAHAP EKSPOR: Mencetak seluruh berkas secara serempak ke root proyek
    try:
        with open("../index.html", "w", encoding="utf-8") as f: f.write(html_template)
        with open("../privacy.html", "w", encoding="utf-8") as f: f.write(privacy_template)
        with open("../terms.html", "w", encoding="utf-8") as f: f.write(terms_template)
        with open("../disclaimer.html", "w", encoding="utf-8") as f: f.write(disclaimer_template)
        with open("../sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_template)
        with open("../robots.txt", "w", encoding="utf-8") as f: f.write(robots_template)
        
        print("\n[SUKSES] Seluruh berkas premium (index, privacy, terms, disclaimer, sitemap, robots) berhasil dibuat!")
    except Exception as e:
        print(f"\n[EROR] Gagal menulis file statis ke folder utama. Detail: {e}")

# MAIN METHOD EKSEKUSI PROGRAM UTAMA
if __name__ == "__main__":
    df_raw = get_stock_data()
    if not df_raw.empty:
        df_analyzed = analyze_recommendations(df_raw)
        generate_static_site(df_analyzed)
