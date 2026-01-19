import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

# --- ページ設定 ---
st.set_page_config(page_title="全国気温 3D Map", layout="wide")
st.title("日本全国の現在の気温 3Dカラムマップ")

# 日本全国47都道府県庁所在地のデータ
prefectural_capitals = {
    'Sapporo':   {'lat': 43.0621, 'lon': 141.3544}, 'Aomori':    {'lat': 40.8244, 'lon': 140.7400},
    'Morioka':   {'lat': 39.7020, 'lon': 141.1545}, 'Sendai':    {'lat': 38.2682, 'lon': 140.8694},
    'Akita':     {'lat': 39.7186, 'lon': 140.1024}, 'Yamagata':  {'lat': 38.2554, 'lon': 140.3396},
    'Fukushima': {'lat': 37.7608, 'lon': 140.4748}, 'Mito':      {'lat': 36.3659, 'lon': 140.4715},
    'Utsunomiya':{'lat': 36.5551, 'lon': 139.8828}, 'Maebashi':  {'lat': 36.3895, 'lon': 139.0634},
    'Saitama':   {'lat': 35.8617, 'lon': 139.6455}, 'Chiba':     {'lat': 35.6074, 'lon': 140.1065},
    'Tokyo':     {'lat': 35.6895, 'lon': 139.6917}, 'Yokohama':  {'lat': 35.4437, 'lon': 139.6380},
    'Niigata':   {'lat': 37.9022, 'lon': 139.0236}, 'Toyama':    {'lat': 36.6959, 'lon': 137.2137},
    'Kanazawa':  {'lat': 36.5613, 'lon': 136.6562}, 'Fukui':     {'lat': 36.0641, 'lon': 136.2196},
    'Kofu':      {'lat': 35.6644, 'lon': 138.5683}, 'Nagano':    {'lat': 36.6486, 'lon': 138.1948},
    'Gifu':      {'lat': 35.4233, 'lon': 136.7607}, 'Shizuoka':  {'lat': 34.9756, 'lon': 138.3828},
    'Nagoya':    {'lat': 35.1815, 'lon': 136.9066}, 'Tsu':       {'lat': 34.7186, 'lon': 136.5057},
    'Otsu':      {'lat': 35.0179, 'lon': 135.8540}, 'Kyoto':     {'lat': 35.0116, 'lon': 135.7681},
    'Osaka':     {'lat': 34.6937, 'lon': 135.5023}, 'Kobe':      {'lat': 34.6901, 'lon': 135.1955},
    'Nara':      {'lat': 34.6851, 'lon': 135.8048}, 'Wakayama':  {'lat': 34.2304, 'lon': 135.1707},
    'Tottori':   {'lat': 35.5011, 'lon': 134.2351}, 'Matsue':    {'lat': 35.4681, 'lon': 133.0488},
    'Okayama':   {'lat': 34.6555, 'lon': 133.9198}, 'Hiroshima': {'lat': 34.3853, 'lon': 132.4553},
    'Yamaguchi': {'lat': 34.1783, 'lon': 131.4737}, 'Tokushima': {'lat': 34.0702, 'lon': 134.5548},
    'Takamatsu': {'lat': 34.3428, 'lon': 134.0466}, 'Matsuyama': {'lat': 33.8392, 'lon': 132.7656},
    'Kochi':     {'lat': 33.5588, 'lon': 133.5312}, 'Fukuoka':   {'lat': 33.5904, 'lon': 130.4017},
    'Saga':      {'lat': 33.2494, 'lon': 130.2974}, 'Nagasaki':  {'lat': 32.7450, 'lon': 129.8739},
    'Kumamoto':  {'lat': 32.7900, 'lon': 130.7420}, 'Oita':      {'lat': 33.2381, 'lon': 131.6119},
    'Miyazaki':  {'lat': 31.9110, 'lon': 131.4240}, 'Kagoshima': {'lat': 31.5600, 'lon': 130.5580},
    'Naha':      {'lat': 26.2124, 'lon': 127.6809}
}

# --- データ取得関数 ---
@st.cache_data(ttl=600)
def fetch_weather_data():
    weather_info = []
    BASE_URL = 'https://api.open-meteo.com/v1/forecast'
    
    # プログレスバーの表示（地点数が多いので）
    progress_bar = st.progress(0)
    total_cities = len(prefectural_capitals)
    
    for i, (city, coords) in enumerate(prefectural_capitals.items()):
        params = {
            'latitude':  coords['lat'],
            'longitude': coords['lon'],
            'current': 'temperature_2m'
            # timezoneパラメータと時刻取得処理を削除しました
        }
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            weather_info.append({
                'City': city,
                'lat': coords['lat'],
                'lon': coords['lon'],
                'Temperature': data['current']['temperature_2m']
            })
        except Exception as e:
            # エラーが出ても止まらずに進むようにする
            print(f"Error fetching {city}: {e}")
        
        # プログレスバーの更新
        progress_bar.progress((i + 1) / total_cities)
            
    progress_bar.empty() # 完了したらバーを消す
    return pd.DataFrame(weather_info)

# データの取得
with st.spinner('日本全国の気温データを取得中...'):
    df = fetch_weather_data()

# 気温を高さ（メートル）に変換
df['elevation'] = df['Temperature'] * 3000

# --- メインレイアウト ---
col1, col2 = st.columns([1, 3]) # 地図をより大きく見せるため比率を変更

with col1:
    st.subheader("全国の気温")
    # 高さ調整を行い、スクロール可能な表にする
    st.dataframe(
        df[['City', 'Temperature']], 
        use_container_width=True,
        height=600 
    )
    
    if st.button('データを更新'):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.subheader("3D カラムマップ")

    # Pydeck の設定（日本全体が見えるように視点を変更）
    view_state = pdk.ViewState(
        latitude=36.0,    # 日本の中心付近
        longitude=138.0,  
        zoom=4.5,         # 全国が入るようにズームアウト
        pitch=45,
        bearing=0
    )

    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position='[lon, lat]',
        get_elevation='elevation',
        radius=10000,      # 全国規模だと重なるため、半径を少し小さく調整(12km->10km)
        get_fill_color='[255, 100, 0, 180]',
        pickable=True,
        auto_highlight=True,
    )

    # 描画
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{City}</b><br>気温: {Temperature}°C",
            "style": {"color": "white"}
        }
    ))
