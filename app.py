import streamlit as st
import pandas as pd
import glob
import os

# 1. Page Configuration
st.set_page_config(
    page_title="CarVault | Premium Used Car Search",
    page_icon="🏎️", 
    layout="wide"
)

# 2. Data Loading Function
@st.cache_data
def load_data():
    all_files = glob.glob("*.csv")
    city_dataframes = []
    
    for file in all_files:
        try:
            df = pd.read_csv(file)
            city_name = file.split('_')[1].split('.')[0].capitalize() if '_' in file else "Unknown"
            df['city_label'] = city_name
            city_dataframes.append(df)
        except:
            continue
            
    if not city_dataframes:
        return None
        
    full_df = pd.concat(city_dataframes, ignore_index=True)
    full_df = full_df.fillna("N/A")
    
    # Optimize numeric price extraction
    full_df['price_numeric'] = (
        full_df['price']
        .astype(str)
        .str.extract(r'(\d+\.?\d*)')[0]
        .astype(float)
        .fillna(0)
    )
    
    # Precompute lowercase names (BIG performance boost)
    full_df['name_lower'] = full_df['name'].astype(str).str.lower()

    return full_df


# 🚀 Cached Filter Function (MAJOR FIX)
@st.cache_data
def filter_data(view_df, search_query, price_range, selected_fuels, selected_trans, sort_choice):
    
    search_query = search_query.lower()

    mask = (
        (view_df['name_lower'].str.contains(search_query, na=False)) &
        (view_df['price_numeric'] >= price_range[0]) &
        (view_df['price_numeric'] <= price_range[1])
    )

    if selected_fuels:
        mask = mask & (view_df['fuel'].isin(selected_fuels))
    if selected_trans:
        mask = mask & (view_df['transmission'].isin(selected_trans))

    filtered_df = view_df[mask].copy()

    if sort_choice == "Low to High":
        filtered_df = filtered_df.sort_values("price_numeric", ascending=True)
    elif sort_choice == "High to Low":
        filtered_df = filtered_df.sort_values("price_numeric", ascending=False)

    return filtered_df


def main():
    st.title("🏎️ CarVault Search Engine")
    st.caption("Aggregated car listings with a hard-reset sync")
    st.markdown("---")

    # --- HARD RESET LOGIC ---
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    df = load_data()
    
    if df is None:
        st.warning("⚠️ No CSV files found. Please run your scrapers first.")
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filter Panel")

    # 1. City Selection
    available_cities = ["All Cities"] + sorted(df['city_label'].unique().tolist())
    selected_city = st.sidebar.selectbox("Location", available_cities, index=0, key="city_box")
    
    if selected_city == "All Cities":
        view_df = df
    else:
        view_df = df[df['city_label'] == selected_city]

    # 2. FILTER FORM
    with st.sidebar.form("filter_form", clear_on_submit=False):
        search_query = st.text_input("Search Model", placeholder="e.g. Swift, City...", key="s_query")

        all_fuels = sorted([f for f in view_df['fuel'].unique() if f != "N/A"])
        selected_fuels = st.multiselect("Fuel Type", all_fuels, key="f_type")
        
        all_trans = sorted([t for t in view_df['transmission'].unique() if t != "N/A"])
        selected_trans = st.multiselect("Transmission", all_trans, key="t_type")

        min_p = float(view_df['price_numeric'].min())
        max_p = float(view_df['price_numeric'].max())
        price_range = st.slider("Budget (Lakhs)", min_p, max_p, (min_p, max_p), key="p_slider")

        sort_choice = st.selectbox("Sort Price", ["Default", "Low to High", "High to Low"], key="sort_box")

        submit_button = st.form_submit_button("Apply Filters", use_container_width=True)

    # 🚀 APPLY FILTERS (NOW CACHED)
    filtered_df = filter_data(
        view_df,
        search_query,
        price_range,
        selected_fuels,
        selected_trans,
        sort_choice
    )

    # --- DISPLAY AREA ---
    display_loc = "All Cities" if selected_city == "All Cities" else selected_city
    st.write(f"### Results for {display_loc} ({len(filtered_df)} Listings)")
    
    if filtered_df.empty:
        st.info("No cars match your current filters.")
    else:
        cols = st.columns(3)

        # 🚀 LIMIT RENDERING (PREVENT UI FREEZE)
        for index, row in filtered_df.head(30).reset_index().iterrows():
            with cols[index % 3]:
                with st.container(border=True):
                    img_url = row.get('image', "N/A") 
                    dummy_img = "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=400"
                    
                    if isinstance(img_url, str) and img_url.startswith("http"):
                        st.image(img_url, use_container_width=True)
                    else:
                        st.image(dummy_img, use_container_width=True)

                    st.subheader(row['name'])
                    
                    c1, c2 = st.columns([1, 1.2])
                    c1.metric("Price", row['price'])
                    
                    loc_display = row.get('location', row['city_label'])
                    if loc_display == "N/A":
                        loc_display = row['city_label']
                    c2.markdown(f"📍 **Loc**\n\n{loc_display}")
                    
                    st.write(f"⚙️ {row['kilometer']} • {row['fuel']} • {row['transmission']}")
                    
                    car_link = row.get('link', "N/A")
                    if isinstance(car_link, str) and car_link.startswith("http"):
                        st.link_button("View Details ↗️", car_link, use_container_width=True)
                    else:
                        st.button("Link Unavailable", disabled=True, use_container_width=True)


if __name__ == "__main__":
    main()
