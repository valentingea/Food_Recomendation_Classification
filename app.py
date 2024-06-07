import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import joblib

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

left_pane, right_pane = st.columns(2)
if not st.session_state["authentication_status"]:
    with left_pane:
            option = st.selectbox("Please select an option:", ["Login", "Register"])
    with right_pane:
        if option == "Login":
            name, state, username = authenticator.login()
            if st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')
            elif st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')
        elif option == "Register":
            try:
                email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(pre_authorization=False)
                if email_of_registered_user:
                    st.success('User registered successfully')
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
            except Exception as e:
                st.error(e)

# Fungsi untuk memuat model yang disimpan
model = joblib.load('best_model.pkl')

# Memuat data makanan
makanan_df = pd.read_csv("data_makanan.csv")

# Kamus pemetaan kondisi kesehatan dan jenis kelamin
kondisi_kesehatan_mapping = {
    'Gagal Jantung': 0,
    'Diabetes': 1,
    'Hipertensi': 2,
    'Penyakit Jantung': 3,
    'PPOK': 4,
    'Kanker': 5,
    'Gagal Ginjal Kronis': 6,
    'Radang Sendi': 7
}

jenis_kelamin_mapping = {
    'Pria': 1,
    'Wanita': 0
}

def get_food_recommendations(user_input):
    # Persiapkan DataFrame kosong untuk menyimpan hasil prediksi
    result_df = pd.DataFrame(columns=['id_makanan', 'nama_makanan', 'kategori', 'rekomendasi'])

    # Loop melalui setiap makanan
    for index, row in makanan_df.iterrows():
        # Buat salinan data pengguna untuk makanan tertentu
        data_predict = user_input.copy()
        
        # Tambahkan informasi makanan
        data_predict['id_makanan'] = row['id_makanan']
        data_predict['nama_makanan'] = row['nama_makanan']
        data_predict['kategori'] = row['kategori']
        
        # Lakukan prediksi untuk makanan tertentu
        prediksi = model.predict(data_predict[['Usia', 'Jenis Kelamin', 'Tinggi (cm)', 'Berat (kg)', 'Kondisi Kesehatan', 'id_makanan']])
        
        # Tambahkan hasil prediksi ke DataFrame result_df
        result_df.loc[index] = [row['id_makanan'], row['nama_makanan'], row['kategori'], prediksi[0]]

    # Mengelompokkan makanan berdasarkan kategori
    grouped_makanan = result_df.groupby('kategori')

    # Membuat dictionary untuk menyimpan makanan berdasarkan kategori dan rekomendasinya
    makanan_by_kategori = {'Boleh': {}, 'Tidak Boleh': {}}

    # Mengisi dictionary dengan makanan berdasarkan kategori dan rekomendasinya
    for kategori, data_kategori in grouped_makanan:
        makanan_boleh = data_kategori[data_kategori['rekomendasi'] == 1]['nama_makanan'].tolist()
        makanan_tidak_boleh = data_kategori[data_kategori['rekomendasi'] == 0]['nama_makanan'].tolist()
        makanan_by_kategori['Boleh'][kategori] = makanan_boleh if makanan_boleh else ['']
        makanan_by_kategori['Tidak Boleh'][kategori] = makanan_tidak_boleh if makanan_tidak_boleh else ['']

    return makanan_by_kategori

if st.session_state["authentication_status"]:
    authenticator.logout()
    # Title aplikasi
    st.title('Food Recommendation System')

    # Input user
    st.header('Input User Data')
    age = st.number_input('Usia', min_value=0, max_value=120, value=25)
    gender_str = st.selectbox('Jenis Kelamin', ['Pria', 'Wanita'])
    height = st.number_input('Tinggi (cm)', min_value=0, max_value=250, value=170)
    weight = st.number_input('Berat (kg)', min_value=0, max_value=200, value=70)
    conditions_str = st.selectbox('Kondisi Kesehatan', ['Gagal Jantung', 'Diabetes', 'Hipertensi', 'Penyakit Jantung', 'PPOK', 'Kanker', 'Gagal Ginjal Kronis', 'Radang Sendi'])

    gender = jenis_kelamin_mapping[gender_str]
    conditions = kondisi_kesehatan_mapping[conditions_str]

    # Konversi input user ke dataframe
    user_input = pd.DataFrame({
        'Usia': [age],
        'Jenis Kelamin': [gender],
        'Tinggi (cm)': [height],
        'Berat (kg)': [weight],
        'Kondisi Kesehatan': [conditions]
    })

    # Button untuk mendapatkan rekomendasi
    if st.button('Dapatkan Rekomendasi Makanan'):
        recommendations = get_food_recommendations(user_input)
        
        # Tampilkan hasil rekomendasi
        st.header('Rekomendasi Makanan', divider='rainbow')
        for status, makanan_per_status in recommendations.items():
            st.subheader(f"\nMakanan yang {status} dikonsumsi:")
            data=[]
            for kategori, makanan in makanan_per_status.items():
                for item in makanan:
                    data.append({'Kategori': kategori, 'Item': item})
            df = pd.DataFrame(data)
            st.dataframe(df, width=800)
