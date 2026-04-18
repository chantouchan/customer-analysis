#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random

random.seed(42)
np.random.seed(42)

st.set_page_config(
    page_title="シャディギフトモール 価格戦略AI最適化ツール",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("## 🎁 シャディギフトモール")
st.sidebar.markdown("価格戦略AI最適化ツール")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("CSVをアップロード", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    try:
        df = pd.read_csv("sample_products.csv")
        st.sidebar.success("サンプルデータ（918商品）読み込み済み")
    except FileNotFoundError:
        st.error("sample_products.csv が見つかりません。先に generate_sample_shaddy.py を実行してください。")
        st.stop()

st.sidebar.markdown(f"**商品数:** {len(df)}")
if "カテゴリ" in df.columns:
    st.sidebar.markdown(f"**カテゴリ数:** {df['カテゴリ'].nunique()}")
if "月間売上" in df.columns:
    st.sidebar.markdown(f"**月間売上合計:** ¥{df['月間売上'].sum():,.0f}")
if "月間粗利" in df.columns:
    st.sidebar.markdown(f"**月間粗利合計:** ¥{df['月間粗利'].sum():,.0f}")

st.sidebar.markdown("---")
if "カテゴリ" in df.columns:
    cats = ["すべて"] + sorted(df["カテゴリ"].unique().tolist())
    selected_cat = st.sidebar.selectbox("カテゴリで絞り込み", cats)
    if selected_cat != "すべて":
        df = df[df["カテゴリ"] == selected_cat]

if "用途タグ" in df.columns:
    occasions = [
        "すべて", "出産内祝い", "結婚内祝い", "香典返し", "快気祝い",
        "新築内祝い", "出産祝い", "結婚祝い", "誕生日", "母の日",
        "お中元", "お歳暮", "退職祝い",
    ]
    selected_occ = st.sidebar.selectbox("用途で絞り込み", occasions)
    if selected_occ != "すべて":
        df = df[df["用途タグ"].astype(str).str.contains(selected_occ, na=False)]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**絞り込み後:** {len(df)}商品")

st.title("🎁 シャディギフトモール 価格戦略AI最適化ツール")
st.markdown(
    "シャディ様の **6万SKU超** のギフト商品に対して、"
    "AI価格最適化による利益改善をご提案します。"
    "（本デモは918商品のサンプルデータで動作しています）"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 利益漏れ診断", "🤖 AI価格提案", "📈 シミュレーション", "📋 週次アクションプラン", "🧪 値上げ実験トラッカー"]
)

# ===================== Tab 1 =====================
with tab1:
    st.header("利益漏れ診断レポート")

    if "粗利率（%）" in df.columns:
        col1, col2, col3, col4 = st.columns(4)
        avg_margin = df["粗利率（%）"].mean()
        low_cnt = int((df["粗利率（%）"] < 40).sum())
        high_cnt = int((df["粗利率（%）"] >= 55).sum())
        total_profit = df["月間粗利"].sum() if "月間粗利" in df.columns else 0
        col1.metric("平均粗利率", f"{avg_margin:.1f}%")
        col2.metric("粗利率40%未満", f"{low_cnt}商品")
        col3.metric("粗利率55%以上", f"{high_cnt}商品")
        col4.metric("月間粗利合計", f"¥{total_profit:,.0f}")

        st.subheader("粗利率の分布")
        fig_hist = px.histogram(
            df, x="粗利率（%）", nbins=30,
            title="粗利率ヒストグラム",
            color_discrete_sequence=["#E8596E"],
        )
        fig_hist.add_vline(x=40, line_dash="dash", line_color="red", annotation_text="40%ライン")
        st.plotly_chart(fig_hist, use_container_width=True)

    if "カテゴリ" in df.columns and "粗利率（%）" in df.columns:
        st.subheader("カテゴリ別 粗利率ボックスプロット")
        fig_box = px.box(
            df, x="カテゴリ", y="粗利率（%）",
            title="カテゴリ別 粗利率分布",
            color="カテゴリ",
        )
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    if "価格帯" in df.columns and "月間売上" in df.columns:
        st.subheader("価格帯別 売上・粗利")
        tier_order = [
            "~1,000円", "~1,500円", "~2,000円", "~2,500円", "~3,000円",
            "~4,000円", "~5,000円", "~8,000円", "~10,000円",
            "~20,000円", "~30,000円", "30,000円~",
        ]
        tier_df = df.groupby("価格帯").agg(
            商品数=("SKU", "count"),
            月間売上合計=("月間売上", "sum"),
            月間粗利合計=("月間粗利", "sum"),
            平均粗利率=("粗利率（%）", "mean"),
        ).reindex([t for t in tier_order if t in df["価格帯"].values]).reset_index()
        fig_tier = go.Figure()
        fig_tier.add_trace(go.Bar(name="月間売上", x=tier_df["価格帯"], y=tier_df["月間売上合計"], marker_color="#636EFA"))
        fig_tier.add_trace(go.Bar(name="月間粗利", x=tier_df["価格帯"], y=tier_df["月間粗利合計"], marker_color="#EF553B"))
        fig_tier.update_layout(barmode="group", title="価格帯別 月間売上 vs 月間粗利")
        st.plotly_chart(fig_tier, use_container_width=True)

    if "粗利率（%）" in df.columns and "月間売上" in df.columns:
        st.subheader("粗利率ワースト20（売上のある商品）")
        worst = df[df["月間販売数"] > 0].nsmallest(20, "粗利率（%）")[
            ["商品名", "カテゴリ", "販売価格（税込）", "原価", "粗利率（%）", "月間販売数", "月間売上"]
        ]
        st.dataframe(worst, use_container_width=True)

    if "用途タグ" in df.columns and "粗利率（%）" in df.columns:
        st.subheader("用途別 平均粗利率")
        occ_list = [
            "出産内祝い", "結婚内祝い", "香典返し", "快気祝い",
            "新築内祝い", "出産祝い", "結婚祝い", "誕生日",
            "母の日", "お中元", "お歳暮", "退職祝い",
        ]
        occ_data = []
        for o in occ_list:
            mask = df["用途タグ"].astype(str).str.contains(o, na=False)
            if mask.sum() > 0:
                occ_data.append({
                    "用途": o,
                    "商品数": int(mask.sum()),
                    "平均粗利率": round(df.loc[mask, "粗利率（%）"].mean(), 1),
                    "月間売上合計": int(df.loc[mask, "月間売上"].sum()) if "月間売上" in df.columns else 0,
                })
        if occ_data:
            occ_df = pd.DataFrame(occ_data)
            fig_occ = px.bar(
                occ_df, x="用途", y="平均粗利率", text="平均粗利率",
                title="用途別 平均粗利率",
                color="平均粗利率",
                color_continuous_scale="RdYlGn",
            )
            st.plotly_chart(fig_occ, use_container_width=True)
            st.dataframe(occ_df, use_container_width=True)

# ===================== Tab 2 =====================
with tab2:
    st.header("AI価格提案")
    st.markdown(
        "粗利率・販売数・カテゴリ・予算帯を考慮して、AIが最適価格を提案します。"
        "カタログギフトはコース価格固定のため据え置きとします。"
    )

    def ai_price_suggestion(row):
        price = row["販売価格（税込）"]
        margin = row["粗利率（%）"]
        cat = row.get("カテゴリ", "")
        qty = row["月間販売数"]
        if cat == "カタログギフト":
            return pd.Series({
                "AI提案価格": price,
                "価格変動": 0,
                "変動率（%）": 0.0,
                "提案理由": "カタログギフトはコース価格固定",
                "信頼度": 95,
            })
        if margin < 35:
            inc = random.uniform(0.05, 0.12)
            new_p = round(price * (1 + inc), -1)
            reason = f"粗利率{margin:.1f}%→改善必要。{inc*100:.0f}%値上げ提案"
            conf = random.randint(70, 85)
        elif margin < 45 and qty > 20:
            inc = random.uniform(0.03, 0.07)
            new_p = round(price * (1 + inc), -1)
            reason = f"売れ筋（月{qty}個）小幅{inc*100:.0f}%値上げ"
            conf = random.randint(75, 88)
        elif margin >= 55 and qty < 10:
            dec = random.uniform(0.03, 0.08)
            new_p = round(price * (1 - dec), -1)
            reason = f"高粗利率{margin:.1f}%だが販売数少（月{qty}個）。値下げで販促"
            conf = random.randint(60, 75)
        else:
            new_p = price
            reason = "現在価格は適正範囲"
            conf = random.randint(80, 95)
        ceilings = [1000, 1500, 2000, 2500, 3000, 4000, 5000, 8000, 10000, 15000, 20000, 30000, 50000]
        for c in ceilings:
            if new_p > c and price <= c:
                new_p = c
                reason += f"（予算帯¥{c:,}上限で調整）"
                break
        new_p = int(new_p)
        diff = new_p - price
        pct = round(diff / price * 100, 1) if price else 0
        return pd.Series({
            "AI提案価格": new_p,
            "価格変動": diff,
            "変動率（%）": pct,
            "提案理由": reason,
            "信頼度": conf,
        })

    required = {"粗利率（%）", "月間販売数", "販売価格（税込）"}
    if required.issubset(df.columns):
        ai_results = df.apply(ai_price_suggestion, axis=1)
        df_ai = pd.concat([df, ai_results], axis=1)
        changed = df_ai[df_ai["価格変動"] != 0]

        c1, c2, c3 = st.columns(3)
        c1.metric("価格変更対象", f"{len(changed)}商品")
        up = changed[changed["価格変動"] > 0]
        down = changed[changed["価格変動"] < 0]
        c2.metric("値上げ提案", f"{len(up)}商品")
        c3.metric("値下げ提案", f"{len(down)}商品")

        if "月間粗利" in df_ai.columns:
            current_profit = df_ai["月間粗利"].sum()
            df_ai["提案後粗利"] = (df_ai["AI提案価格"] - df_ai["原価"]) * df_ai["月間販売数"]
            new_profit = df_ai["提案後粗利"].sum()
            improvement = new_profit - current_profit
            st.metric(
                "月間粗利改善見込み",
                f"¥{improvement:,.0f}",
                delta=f"{improvement/current_profit*100:.1f}%" if current_profit else "",
            )
            st.markdown(f"**年間換算改善額: ¥{improvement*12:,.0f}**")

        st.subheader("価格変更提案一覧")
        show_cols = [
            "商品名", "カテゴリ", "販売価格（税込）", "AI提案価格",
            "価格変動", "変動率（%）", "粗利率（%）", "月間販売数", "提案理由", "信頼度",
        ]
        show_cols = [c for c in show_cols if c in df_ai.columns]
        st.dataframe(
            df_ai[df_ai["価格変動"] != 0][show_cols].sort_values("価格変動", ascending=False),
            use_container_width=True,
            height=500,
        )

        csv_data = df_ai.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 AI提案結果CSVダウンロード",
            csv_data,
            f"shaddy_ai_price_proposal_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
        )

# ===================== Tab 3 =====================
with tab3:
    st.header("価格変更シミュレーション")
    st.markdown("価格変更率と需要弾力性を設定し、売上・粗利への影響をシミュレーションします。")
    st.info("💡 ギフト商品は一般消費財より価格弾力性が低い傾向にあります（予算ありきで購入）。弾力性 -0.2〜-0.4 が目安です。")

    sim_col1, sim_col2 = st.columns(2)
    price_change_pct = sim_col1.slider("価格変更率（%）", -20, 20, 5, 1)
    elasticity = sim_col2.slider("需要弾力性", -1.0, 0.0, -0.3, 0.05)

    if {"販売価格（税込）", "原価", "月間販売数"}.issubset(df.columns):
        sim_df = df.copy()
        sim_df["新価格"] = (sim_df["販売価格（税込）"] * (1 + price_change_pct / 100)).round(0).astype(int)
        sim_df["新販売数"] = (sim_df["月間販売数"] * (1 + elasticity * price_change_pct / 100)).round(0).astype(int)
        sim_df["新販売数"] = sim_df["新販売数"].clip(lower=0)
        sim_df["現在月間売上"] = sim_df["販売価格（税込）"] * sim_df["月間販売数"]
        sim_df["新月間売上"] = sim_df["新価格"] * sim_df["新販売数"]
        sim_df["現在月間粗利"] = (sim_df["販売価格（税込）"] - sim_df["原価"]) * sim_df["月間販売数"]
        sim_df["新月間粗利"] = (sim_df["新価格"] - sim_df["原価"]) * sim_df["新販売数"]

        cur_rev = sim_df["現在月間売上"].sum()
        new_rev = sim_df["新月間売上"].sum()
        cur_pro = sim_df["現在月間粗利"].sum()
        new_pro = sim_df["新月間粗利"].sum()

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("現在月間売上", f"¥{cur_rev:,.0f}")
        sc2.metric("新月間売上", f"¥{new_rev:,.0f}", delta=f"¥{new_rev-cur_rev:,.0f}")
        sc3.metric("現在月間粗利", f"¥{cur_pro:,.0f}")
        sc4.metric("新月間粗利", f"¥{new_pro:,.0f}", delta=f"¥{new_pro-cur_pro:,.0f}")

        pct_range = list(range(-10, 11))
        rev_list = []
        pro_list = []
        for p in pct_range:
            np_ = (df["販売価格（税込）"] * (1 + p / 100))
            nq_ = (df["月間販売数"] * (1 + elasticity * p / 100)).clip(lower=0)
            rev_list.append((np_ * nq_).sum())
            pro_list.append(((np_ - df["原価"]) * nq_).sum())
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=pct_range, y=rev_list, name="月間売上", line=dict(color="#636EFA")))
        fig_sim.add_trace(go.Scatter(x=pct_range, y=pro_list, name="月間粗利", line=dict(color="#EF553B")))
        fig_sim.add_vline(x=price_change_pct, line_dash="dash", line_color="green", annotation_text=f"設定値 {price_change_pct}%")
        fig_sim.update_layout(title="価格変更率 vs 売上・粗利", xaxis_title="価格変更率（%）", yaxis_title="金額（円）")
        st.plotly_chart(fig_sim, use_container_width=True)

# ===================== Tab 4 =====================
with tab4:
    st.header("週次アクションプラン")
    st.markdown("データから自動生成された今週の優先アクションです。")

    actions = []
    if {"粗利率（%）", "月間販売数"}.issubset(df.columns):
        low_margin_hot = df[(df["粗利率（%）"] < 40) & (df["月間販売数"] > 20)]
        for _, r in low_margin_hot.nsmallest(5, "粗利率（%）").iterrows():
            actions.append({
                "優先度": "🔴 高",
                "アクション": "値上げテスト開始",
                "対象商品": r["商品名"],
                "カテゴリ": r["カテゴリ"],
                "現在価格": f"¥{r['販売価格（税込）']:,}",
                "粗利率": f"{r['粗利率（%）']:.1f}%",
                "理由": f"月{r['月間販売数']}個売れているのに粗利率{r['粗利率（%）']:.1f}%。5%値上げテスト推奨",
            })

    now = datetime.now()
    month = now.month
    seasonal = []
    if month in [4, 5]:
        seasonal.append({"優先度": "🟡 中", "アクション": "母の日ギフト価格見直し", "対象商品": "母の日関連商品", "カテゴリ": "全カテゴリ", "現在価格": "-", "粗利率": "-", "理由": "母の日需要期。価格感度が下がるため小幅値上げ余地あり"})
    if month in [6, 7]:
        seasonal.append({"優先度": "🟡 中", "アクション": "お中元価格最適化", "対象商品": "お中元関連商品", "カテゴリ": "グルメ・スイーツ", "現在価格": "-", "粗利率": "-", "理由": "お中元シーズン。ギフトセット価格の見直し推奨"})
    if month in [11, 12]:
        seasonal.append({"優先度": "🟡 中", "アクション": "お歳暮価格最適化", "対象商品": "お歳暮関連商品", "カテゴリ": "グルメ・スイーツ", "現在価格": "-", "粗利率": "-", "理由": "お歳暮シーズン。高単価ギフトの需要増"})
    actions.extend(seasonal)

    if "在庫状況" in df.columns:
        low_stock = df[df["在庫状況"] == "在庫僅少"]
        if len(low_stock) > 0:
            actions.append({
                "優先度": "🟡 中",
                "アクション": "在庫僅少商品の価格調整検討",
                "対象商品": f"{len(low_stock)}商品",
                "カテゴリ": "複数",
                "現在価格": "-",
                "粗利率": "-",
                "理由": f"在庫僅少{len(low_stock)}商品。品切れ前に値上げで利益確保、または早期補充",
            })

    actions.append({
        "優先度": "🟢 低",
        "アクション": "カタログ反映準備",
        "対象商品": "EC値上げテスト成功商品",
        "カテゴリ": "全カテゴリ",
        "現在価格": "-",
        "粗利率": "-",
        "理由": "ECで3週間テスト後、月次カタログ更新に反映。次回締切を確認",
    })

    if actions:
        st.dataframe(pd.DataFrame(actions), use_container_width=True, height=400)
    else:
        st.info("現在のデータではアクション提案はありません。")

# ===================== Tab 5 =====================
with tab5:
    st.header("値上げ実験トラッカー")
    st.markdown("EC上で実施中の価格テストを管理・追跡します。")

    experiments = [
        {
            "実験名": "ヨックモック バラエティーギフトS 5%値上げ",
            "対象商品": "ヨックモック バラエティーギフトS",
            "カテゴリ": "グルメ・スイーツ",
            "変更前価格": "¥2,700",
            "変更後価格": "¥2,840",
            "変更率": "+5.2%",
            "開始日": "2026-03-25",
            "経過日数": "22日",
            "ステータス": "🟢 テスト中",
            "変更前販売数/週": 45,
            "変更後販売数/週": 43,
            "販売数変化": "-4.4%",
            "週次利益変動": "+¥4,520/週",
            "備考": "出産内祝い用途。販売数ほぼ維持、利益改善中。",
        },
        {
            "実験名": "P&G アリエール ジェルボール ギフト 8%値上げ",
            "対象商品": "P&G アリエール ジェルボール ギフトセット",
            "カテゴリ": "石鹸・洗剤・入浴剤",
            "変更前価格": "¥2,200",
            "変更後価格": "¥2,380",
            "変更率": "+8.2%",
            "開始日": "2026-03-18",
            "経過日数": "29日",
            "ステータス": "🟢 テスト中",
            "変更前販売数/週": 38,
            "変更後販売数/週": 35,
            "販売数変化": "-7.9%",
            "週次利益変動": "+¥6,920/週",
            "備考": "香典返し用途。弾力性低く利益改善。3週間経過でカタログ反映検討。",
        },
        {
            "実験名": "今治謹製 極上タオル 3%値上げ",
            "対象商品": "今治謹製 極上タオル バスタオル 木箱入",
            "カテゴリ": "タオル・寝具",
            "変更前価格": "¥5,500",
            "変更後価格": "¥5,670",
            "変更率": "+3.1%",
            "開始日": "2026-04-01",
            "経過日数": "15日",
            "ステータス": "✅ 成功（カタログ反映済）",
            "変更前販売数/週": 28,
            "変更後販売数/週": 27,
            "販売数変化": "-3.6%",
            "週次利益変動": "+¥3,810/週",
            "備考": "結婚内祝い定番。販売数影響なし。4月カタログに反映完了。",
        },
        {
            "実験名": "ロクシタン ハンドクリーム 10%値下げ",
            "対象商品": "ロクシタン ハンドクリームコレクション",
            "カテゴリ": "コスメ・ファッション",
            "変更前価格": "¥3,520",
            "変更後価格": "¥3,170",
            "変更率": "-9.9%",
            "開始日": "2026-04-08",
            "経過日数": "8日",
            "ステータス": "🔵 観察中",
            "変更前販売数/週": 8,
            "変更後販売数/週": 12,
            "販売数変化": "+50.0%",
            "週次利益変動": "-¥3,810/週",
            "備考": "母の日需要狙い値下げ。販売数増加中だが利益は減少。2週目判断。",
        },
    ]

    st.dataframe(pd.DataFrame(experiments), use_container_width=True, height=300)

    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("実施中の実験", "2件")
    ec2.metric("成功→カタログ反映", "1件")
    ec3.metric("週次利益改善合計", "+¥11,440/週", delta="年間換算 +¥594,880")

    st.subheader("新規実験登録（デモ）")
    with st.form("new_experiment"):
        exp_name = st.text_input("実験名")
        exp_product = st.text_input("対象商品名")
        exp_price_before = st.number_input("変更前価格", min_value=0, value=3000)
        exp_price_after = st.number_input("変更後価格", min_value=0, value=3150)
        exp_note = st.text_area("備考")
        submitted = st.form_submit_button("実験を登録")
        if submitted:
            st.success(f"実験「{exp_name}」を登録しました（デモ）。実運用時はDBに保存されます。")

st.markdown("---")
st.markdown(
    "**シャディギフトモール 価格戦略AI最適化ツール**（プロトタイプ版） | "
    "実データCSVをインポートすることで全6万SKUの分析が可能です。 | "
    f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
