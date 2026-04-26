import streamlit as st
import datetime
import pandas as pd
import csv
from pathlib import Path
import io
import pytz
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# Funkcja pobierająca czas w Polsce
def get_now_pl():
    tz = pytz.timezone('Europe/Warsaw')
    return datetime.datetime.now(tz)

# Funkcja usuwająca polskie znaki dla PDF (Helvetica nie wspiera Unicode)
def usun_polskie_znaki(tekst):
    if not tekst or not isinstance(tekst, str):
        return str(tekst)
    mapping = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    for pol, lat in mapping.items():
        tekst = tekst.replace(pol, lat)
    return tekst

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Karta Drogowa PRO", 
    page_icon="🚛", 
    layout="centered",
    initial_sidebar_state="auto"
)

# Inicjalizacja stanu na samym początku (zapobiega pętlom)
if 'dane_k' not in st.session_state:
    st.session_state.dane_k = {"kierowca": "", "kierowca2": "", "nr_rej": "", "nr_nac": ""}

# Połączenie z Google Sheets (jeśli skonfigurowane w Secrets)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    USE_GSHEETS = True
except Exception as e:
    st.error(f"KRYTYCZNY BŁĄD KONFIGURACJI SECRETS: {e}")
    USE_GSHEETS = False

# --- STAŁE I PLIKI ---
PLIK_CSV = Path("karta_nowoczesna.csv")
NAGLOWKI = ["Data", "Przyjazd", "Odjazd", "Kod", "Miasto", "Firma", "Zaladunek", "Rozladunek", "Granica", "Paliwo", "Licznik", "Komentarz"]

# --- FUNKCJE POMOCNICZE ---

def generuj_pdf(df, dane_kierowcy):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    
    # Próba załadowania polskiej czcionki
    try:
        pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
        pdf.add_font("ArialBD", "", r"C:\Windows\Fonts\arialbd.ttf")
        font_name = "Arial"
        font_bold = "ArialBD"
    except:
        font_name = "Helvetica"
    
    # --- NAGŁÓWEK (PRO) ---
    pdf.set_fill_color(30, 116, 190)
    pdf.rect(0, 0, 297, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 20)
    pdf.text(10, 17, usun_polskie_znaki("KARTA DROGOWA"))
    
    pdf.set_font("helvetica", "", 10)
    pdf.text(230, 17, usun_polskie_znaki(f"Wygenerowano: {datetime.date.today().strftime('%d.%m.%Y')}"))
    
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    
    # Ramka z danymi (2 kolumny)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    
    # Rząd 1
    pdf.cell(45, 8, usun_polskie_znaki(" Kierowca 1:"), 1, 0, "L", True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 8, f" {usun_polskie_znaki(dane_kierowcy.get('kierowca', ''))}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(45, 8, usun_polskie_znaki(" Nr rej. ciagnik:"), 1, 0, "L", True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f" {usun_polskie_znaki(dane_kierowcy.get('nr_rej', ''))}", 1, 1, "L")
    
    # Rząd 2
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(45, 8, usun_polskie_znaki(" Kierowca 2:"), 1, 0, "L", True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 8, f" {usun_polskie_znaki(dane_kierowcy.get('kierowca2', ''))}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(45, 8, usun_polskie_znaki(" Nr naczepy:"), 1, 0, "L", True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f" {usun_polskie_znaki(dane_kierowcy.get('nr_nac', ''))}", 1, 1, "L")
    
    pdf.ln(5)
    
    # --- TABELA ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(30, 116, 190)
    pdf.set_text_color(255, 255, 255)
    
    col_widths = [8, 18, 15, 15, 18, 35, 30, 10, 10, 10, 15, 25, 68]
    cols = ["Lp", "Data", "Przyjazd", "Odjazd", "Kod", "Miejscowosc", "Firma", "Zal", "Roz", "Gra", "Paliwo", "Licznik", "Uwagi"]
    
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 8, usun_polskie_znaki(col), border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    
    for index, row in df.iterrows():
        # Kolorowanie co drugiego wiersza dla lepszej czytelnosci
        fill = index % 2 == 0
        if fill: pdf.set_fill_color(250, 250, 250)
        else: pdf.set_fill_color(255, 255, 255)

        pdf.cell(col_widths[0], 7, str(index + 1), border=1, align="C", fill=True)
        pdf.cell(col_widths[1], 7, usun_polskie_znaki(str(row["Data"])), border=1, align="C", fill=True)
        pdf.cell(col_widths[2], 7, usun_polskie_znaki(str(row["Przyjazd"])), border=1, align="C", fill=True)
        pdf.cell(col_widths[3], 7, usun_polskie_znaki(str(row["Odjazd"])), border=1, align="C", fill=True)
        pdf.cell(col_widths[4], 7, usun_polskie_znaki(str(row["Kod"])), border=1, align="C", fill=True)
        pdf.cell(col_widths[5], 7, f" {usun_polskie_znaki(str(row['Miasto'])[:20])}", border=1, fill=True)
        pdf.cell(col_widths[6], 7, f" {usun_polskie_znaki(str(row['Firma'])[:18])}", border=1, fill=True)
        
        pdf.cell(col_widths[7], 7, "X" if row["Zaladunek"] else "", border=1, align="C", fill=True)
        pdf.cell(col_widths[8], 7, "X" if row["Rozladunek"] else "", border=1, align="C", fill=True)
        pdf.cell(col_widths[9], 7, "X" if row["Granica"] else "", border=1, align="C", fill=True)
        
        paliwo_val = str(row["Paliwo"]) if pd.notna(row["Paliwo"]) and row["Paliwo"] != "" and row["Paliwo"] != 0 else ""
        if paliwo_val == "nan": paliwo_val = ""
        pdf.cell(col_widths[10], 7, paliwo_val, border=1, align="C", fill=True)
        
        # Licznik jako liczba całkowita
        try:
            licznik_val = str(int(float(row["Licznik"])))
        except:
            licznik_val = str(row["Licznik"])
        pdf.cell(col_widths[11], 7, licznik_val, border=1, align="C", fill=True)
        
        pdf.cell(col_widths[12], 7, f" {usun_polskie_znaki(str(row['Komentarz'])[:45])}", border=1, fill=True)
        pdf.ln()
    
    # --- PODSUMOWANIE ---
    pdf.ln(5)
    curr_y = pdf.get_y()
    
    # Ramka podsumowania
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, curr_y, 100, 30, 'F')
    pdf.set_font("helvetica", "B", 10)
    pdf.text(15, curr_y + 7, usun_polskie_znaki("PODSUMOWANIE TRASY"))
    pdf.set_font("helvetica", "", 9)
    
    trasa = 0
    if len(df) > 1:
        liczniki = pd.to_numeric(df['Licznik'], errors='coerce').dropna()
        if not liczniki.empty: trasa = int(liczniki.max() - liczniki.min())
    
    paliwo_suma = pd.to_numeric(df['Paliwo'], errors='coerce').fillna(0).sum()
    
    pdf.text(15, curr_y + 15, usun_polskie_znaki(f"Suma kilometrow: {trasa} km"))
    pdf.text(15, curr_y + 21, usun_polskie_znaki(f"Zatankowano: {paliwo_suma:.2f} L"))
    
    try:
        l_min = int(float(df['Licznik'].min()))
        l_max = int(float(df['Licznik'].max()))
        pdf.text(15, curr_y + 27, usun_polskie_znaki(f"Stan licznika: {l_min} -> {l_max}"))
    except:
        pass
    
    # Podpisy
    pdf.set_font("helvetica", "", 8)
    pdf.text(140, curr_y + 25, "......................................................................")
    pdf.text(155, curr_y + 29, usun_polskie_znaki("Podpis kierowcy"))
    
    pdf.text(210, curr_y + 25, "......................................................................")
    pdf.text(215, curr_y + 29, usun_polskie_znaki("Pieczatka firmy / Uwagi dyspozytora"))
    
    return bytes(pdf.output())

def inicjalizuj_plik():
    if not PLIK_CSV.exists():
        df = pd.DataFrame(columns=NAGLOWKI)
        df.to_csv(PLIK_CSV, index=False, sep=";", encoding="utf-8")

def pobierz_dane():
    inicjalizuj_plik()
    
    # Próba pobrania z Google Sheets
    if USE_GSHEETS:
        try:
            df = conn.read(ttl=0)
            # Konwersja dla edytora: X -> True
            for col in ["Zaladunek", "Rozladunek", "Granica"]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: True if str(x).upper() == "X" else False)
            return df
        except Exception:
            st.warning("Problem z połączeniem z Google Sheets. Korzystam z kopii lokalnej.")

    # Fallback do CSV
    df = pd.read_csv(PLIK_CSV, sep=";", encoding="utf-8")
    
    # Inteligentne czyszczenie kolumn
    def clean_number(val):
        if pd.isna(val) or val == "": return ""
        try:
            f_val = float(val)
            if f_val == 0: return ""
            if f_val.is_integer(): return str(int(f_val))
            return str(f_val)
        except:
            return str(val)

    df["Kod"] = df["Kod"].apply(clean_number)
    df["Licznik"] = df["Licznik"].apply(clean_number)

    for col in ["Zaladunek", "Rozladunek", "Granica"]:
        df[col] = df[col].apply(lambda x: True if x == "X" else False)
    return df

def zapisz_dane(df):
    df_to_save = df.copy()
    # Konwersja True -> X dla zapisu
    for col in ["Zaladunek", "Rozladunek", "Granica"]:
        if col in df_to_save.columns:
            df_to_save[col] = df_to_save[col].apply(lambda x: "X" if x is True or str(x).upper() == "X" else "")
    
    df_to_save.to_csv(PLIK_CSV, index=False, sep=";", encoding="utf-8")
    
    if USE_GSHEETS:
        try:
            conn.update(data=df_to_save)
            st.toast("Zapisano w Google Sheets! ☁️")
        except Exception:
            st.error("Błąd zapisu w Google Sheets.")

def pobierz_ostatni_licznik():
    df = pobierz_dane()
    if not df.empty:
        try:
            liczniki = pd.to_numeric(df["Licznik"], errors='coerce').dropna()
            if not liczniki.empty:
                return int(liczniki.max())
        except:
            return 0
    return 0

def dodaj_wpis(nowy_wpis):
    df = pobierz_dane()
    # Konwersja booleana na X dla spójności zapisu
    for col in ["Zaladunek", "Rozladunek", "Granica"]:
        if isinstance(nowy_wpis.get(col), bool):
            nowy_wpis[col] = "X" if nowy_wpis[col] else ""
            
    nowy_df = pd.DataFrame([nowy_wpis])
    df_final = pd.concat([df, nowy_df], ignore_index=True)
    zapisz_dane(df_final)

# --- NAWIGACJA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2555/2555013.png", width=100)
    st.title("Menu")
    strona = st.radio("Wybierz sekcje:", ["➕ Dodaj Wpis", "📋 Historia i Edycja", "📊 Raporty i Eksport", "⚙️ Ustawienia"])
    st.divider()
    
    # Sekcja informacyjna
    st.info("Aplikacja zoptymalizowana pod iPhone'a. Używaj pionowo.")

# --- SEKCJA 4: USTAWIENIA (NOWE) ---
if strona == "⚙️ Ustawienia":
    st.markdown('<div class="header-style">⚙️ Ustawienia Raportu</div>', unsafe_allow_html=True)
    with st.form("ustawienia_form"):
        st.write("Wprowadź dane do nagłówka PDF:")
        k1 = st.text_input("Imię i Nazwisko kierowcy 1", value=st.session_state.dane_k['kierowca'])
        k2 = st.text_input("Imię i Nazwisko kierowcy 2", value=st.session_state.dane_k['kierowca2'])
        rej = st.text_input("Numer Rejestracyjny ciągnika", value=st.session_state.dane_k['nr_rej'])
        nac = st.text_input("Numer Naczepy", value=st.session_state.dane_k['nr_nac'])
        
        if st.form_submit_button("💾 ZAPISZ USTAWIENIA", use_container_width=True):
            st.session_state.dane_k = {
                "kierowca": k1,
                "kierowca2": k2,
                "nr_rej": rej,
                "nr_nac": nac
            }
            st.success("✅ Ustawienia zapisane!")
            st.rerun()

# --- SEKCJA 1: DODAWANIE WPISÓW ---
elif strona == "➕ Dodaj Wpis":
    st.markdown('<div class="header-style">🚛 Nowy Wpis do Karty</div>', unsafe_allow_html=True)
    
    tab_firma, tab_granica, tab_paliwo = st.tabs(["🏭 Firma", "🛂 Granica", "⛽ Paliwo"])
    
    ostatni_licznik = pobierz_ostatni_licznik()

    with tab_firma:
        with st.form("form_firma", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data", get_now_pl().date())
                przyj = st.time_input("Przyjazd", get_now_pl().time(), key="time_p", step=60)
                odj = st.time_input("Odjazd", get_now_pl().time(), key="time_o", step=60)
            with col2:
                firma = st.text_input("Nazwa firmy", placeholder="np. Amazon, DHL")
                miasto = st.text_input("Miejscowość")
                kod = st.text_input("Kod pocztowy")
            
            st.write("Operacja:")
            c1, c2 = st.columns(2)
            zal = c1.checkbox("Załadunek")
            roz = c2.checkbox("Rozładunek")
            
            licznik = st.number_input("Stan licznika (km)", min_value=ostatni_licznik, value=ostatni_licznik, step=1)
            koment = st.text_input("Komentarz / Uwagi")
            
            submit = st.form_submit_button("💾 ZAPISZ WPIS FIRMY", use_container_width=True)
            if submit:
                wpis = {
                    "Data": data.strftime("%d.%m.%Y"), "Przyjazd": przyj.strftime("%H:%M"),
                    "Odjazd": odj.strftime("%H:%M"), "Kod": kod, "Miasto": miasto, "Firma": firma,
                    "Zaladunek": zal, "Rozladunek": roz,
                    "Granica": False, "Paliwo": "", "Licznik": licznik, "Komentarz": koment
                }
                dodaj_wpis(wpis)
                st.success(f"Dodano: {firma}")
                st.balloons()

    with tab_granica:
        with st.form("form_granica", clear_on_submit=True):
            st.subheader("Przekroczenie Granicy")
            col1, col2 = st.columns(2)
            with col1:
                data_g = st.date_input("Data", get_now_pl().date(), key="g_date")
                czas_g = st.time_input("Godzina", get_now_pl().time(), key="g_time", step=60)
            with col2:
                kraj_relacja = st.text_input("Relacja (np. PL/D, D/NL)", placeholder="np. PL/D")
                miasto_g = st.text_input("Miejscowość (np. Świecko, Zgorzelec)")
            
            licznik_g = st.number_input("Stan licznika (km)", min_value=ostatni_licznik, value=ostatni_licznik, key="g_km")
            
            submit_g = st.form_submit_button("🛂 ZAPISZ GRANICE", use_container_width=True)
            if submit_g:
                wpis = {
                    "Data": data_g.strftime("%d.%m.%Y"), "Przyjazd": czas_g.strftime("%H:%M"),
                    "Odjazd": czas_g.strftime("%H:%M"), "Kod": kraj_relacja, "Miasto": miasto_g, "Firma": "GRANICA",
                    "Zaladunek": False, "Rozladunek": False, "Granica": True, "Paliwo": "", 
                    "Licznik": licznik_g, "Komentarz": f"Przejście: {kraj_relacja}"
                }
                dodaj_wpis(wpis)
                st.success(f"Zapisano granicę: {kraj_relacja} w {miasto_g}")

    with tab_paliwo:
        with st.form("form_paliwo", clear_on_submit=True):
            st.subheader("Tankowanie")
            col1, col2 = st.columns(2)
            with col1:
                data_p = st.date_input("Data", get_now_pl().date(), key="p_date")
                litry = st.number_input("Ilosc litrów (L)", min_value=0.0, step=0.1)
            with col2:
                stacja = st.text_input("Stacja / Miasto")
                licznik_p = st.number_input("Stan licznika (km)", min_value=ostatni_licznik, value=ostatni_licznik, key="p_km")
            
            submit_p = st.form_submit_button("⛽ ZAPISZ TANKOWANIE", use_container_width=True)
            if submit_p:
                wpis = {
                    "Data": data_p.strftime("%d.%m.%Y"), "Przyjazd": "", "Odjazd": "", 
                    "Kod": "", "Miasto": stacja, "Firma": "TANKOWANIE",
                    "Zaladunek": False, "Rozladunek": False, "Granica": False, "Paliwo": litry, 
                    "Licznik": licznik_p, "Komentarz": f"Tankowanie {litry}L"
                }
                dodaj_wpis(wpis)
                st.success("Zapisano tankowanie!")

# --- SEKCJA 2: HISTORIA I EDYCJA ---
elif strona == "📋 Historia i Edycja":
    st.markdown('<div class="header-style">📋 Historia Wpisów</div>', unsafe_allow_html=True)
    st.info("Tutaj mozesz edytować dane bezpośrednio w tabeli. Nie zapomnij zapisać zmian!")
    
    df = pobierz_dane()
    if not df.empty:
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Zaladunek": st.column_config.CheckboxColumn(),
                "Rozladunek": st.column_config.CheckboxColumn(),
                "Granica": st.column_config.CheckboxColumn()
            }
        )
        
        if st.button("💾 Zapisz zmiany w historii", use_container_width=True):
            zapisz_dane(edited_df)
            st.rerun()
    else:
        st.warning("Brak wpisów w historii.")

# --- SEKCJA 3: RAPORTY ---
elif strona == "📊 Raporty i Eksport":
    st.markdown('<div class="header-style">📊 Generowanie Raportu</div>', unsafe_allow_html=True)
    
    df = pobierz_dane()
    if not df.empty:
        st.write("Podglad aktualnych danych:")
        st.dataframe(df.tail(10)) 
        
        st.divider()
        st.subheader("Pobierz Raport")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Przekazujemy dane kierowcy do generatora PDF
                pdf_data = generuj_pdf(df, st.session_state.dane_k)
                st.download_button(
                    label="📄 Pobierz Raport PDF",
                    data=pdf_data,
                    file_name=f"karta_drogowa_{datetime.date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Bład przy generowaniu PDF: {e}")

        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Karta_Drogowa')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 Pobierz Excel (.xlsx)",
                data=excel_data,
                file_name=f"karta_drogowa_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Statystyki (widoczne w aplikacji)
        st.divider()
        st.subheader("Szybkie statystyki")
        col1, col2, col3 = st.columns(3)
        col1.metric("Liczba wpisów", len(df))
        
        paliwo_suma = pd.to_numeric(df['Paliwo'], errors='coerce').fillna(0).sum()
        col2.metric("Suma paliwa", f"{paliwo_suma:.1f} L")
        
        trasa = 0
        if len(df) > 1:
            try:
                liczniki = pd.to_numeric(df['Licznik'], errors='coerce').dropna()
                if not liczniki.empty:
                    trasa = int(liczniki.max() - liczniki.min())
            except:
                trasa = 0
        col3.metric("Przejechane km", f"{trasa} km")
    else:
        st.warning("Dodaj pierwsze wpisy, aby móc wygenerować raport.")