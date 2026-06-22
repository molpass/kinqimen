<div align="center">

# 🔮 堅奇門 · KinQiMen

### Python 기문둔갑(奇門遁甲) 排盤 시스템 | Python Qimen Dunjia Divination System

![banner](https://github.com/kentang2017/kinqimen/blob/master/assets/banner.png)

**천년의 현묘한 술법, 한 줄의 코드 · Ancient Wisdom, Modern Code**

[![Python](https://img.shields.io/pypi/pyversions/kinqimen?label=Python&logo=python)](https://pypi.org/project/kinqimen/)
[![PIP Version](https://img.shields.io/pypi/v/kinqimen?label=PyPI&logo=pypi)](https://pypi.org/project/kinqimen/)
[![Downloads](https://img.shields.io/pypi/dm/kinqimen?label=Downloads&logo=pypi&color=blue)](https://pypi.org/project/kinqimen/)
[![License](https://img.shields.io/github/license/kentang2017/kinqimen?label=License)](LICENSE)

**🌐 온라인 排盤(포국) · Live Demo → [kinqimen.streamlitapp.com](https://kinqimen.streamlitapp.com)**

</div>

> 🇰🇷 이 저장소는 **molpass가 포크한 사본**입니다. 원문(中文·English)은 [README.en.md](./README.en.md)를 참고하세요.

---

## 📖 도입 · Introduction

> 기문둔갑(奇門遁甲)은 대육임(大六壬), 태을신수(太乙神數)와 더불어 **중국 3대 신비 예측술**로 불리며, 역대로 천자 곁의 국사(國師)와 군사(軍師)만이 익힐 수 있었다.
>
> *Qimen Dunjia is one of the legendary **Three Arts** of Chinese metaphysical divination — historically reserved for imperial advisors and military strategists.*

**기문둔갑**(奇門遁甲, Qimen Dunjia)은 중국 고대에서 가장 심오한 예측학 중 하나입니다. 낙서구궁(洛書九宮)을 반(盤)으로 삼고, 음양오행·팔괘·천간지지·24절기를 결합하여 시공간이 회전하는 우주 에너지 매트릭스를 구성합니다. 전체 반에는 총 **1,080종의 국(局)**이 있어 매 시진마다 바뀌며, 천·지·인 삼재(三才)의 기운을 정밀하게 포착합니다. 의사결정, 방위, 사업, 그리고 개인의 길흉을 좇고 피하는 데 널리 활용됩니다.

Qimen Dunjia is an ancient Chinese cosmic divination art that maps heaven, earth and human energies onto a 3×3 magic square of **Nine Palaces**. Rotating through **1,080 unique configurations** — one per double-hour — it incorporates yin-yang theory, the Five Elements, Eight Trigrams, Heavenly Stems, Earthly Branches, and the 24 Solar Terms. Used for centuries in military strategy, business decisions, travel planning, and personal forecasting.

---

## ✨ 기능 특징 · Features

| 기능 Feature | 설명 Description |
|---|---|
| 🕐 **시가기문(時家奇門)** Hour-based Qimen | 시진으로 기반(起盤)하는, 가장 흔히 쓰이는 전통 포국 방식 · Classic hour-based divination chart |
| ⏱ **각가기문(刻家奇門)** Minute-based Qimen | 분 단위로 정밀 계산, 정확한 예측에 적합 · High-precision minute-level chart |
| 📜 **금함옥경(金函玉鏡)** Golden Mirror | 금함 일가기문(日家奇門), 고전 일가 포국 · Classic daily Golden Letter Jade Mirror style |
| 🔄 **탁보 / 치윤(拆補 / 置閏)** Two Calculation Methods | 탁보법과 치윤법을 모두 지원하여 각 유파에 유연 대응 · Supports both Chabu & Zhirun methods |
| 🖥 **Web 포국 인터페이스** Web UI | Streamlit 기반 인터랙티브 온라인 포국 · Interactive online chart via Streamlit |
| 🐍 **순수 Python** Pure Python | 가볍고 쓰기 쉬워 어떤 Python 프로젝트에도 임베드 가능 · Lightweight and easy to integrate |

---

## 🚀 설치 · Installation

```bash
pip install sxtwl
pip install kinqimen
```

---

## ⚡ 빠른 시작 · Quickstart

```python
from kinqimen import kinqimen

year, month, day, hour, minute = 2024, 6, 15, 14, 30

# 時家奇門（拆補法） | Hour-based Qimen (Chabu method)
result = kinqimen.Qimen(year, month, day, hour, minute).pan(1)   # 1=拆補, 2=置閏

# 刻家奇門（置閏法） | Minute-based Qimen (Zhirun method)
result = kinqimen.Qimen(year, month, day, hour, minute).pan_minute(2)

# 金函玉鏡日家奇門 | Golden Letter Jade Mirror daily chart
result = kinqimen.Qimen(year, month, day, hour, minute).gpan()

# 綜合排盤（時家 + 金函） | Combined chart (Hour-based + Golden Mirror)
result = kinqimen.Qimen(year, month, day, hour, minute).overall()
```

---

## 🗺 포국 예시 · Chart Preview

```
＼  天蓬神　 │  天芮神　 │  天沖神　／
 ─────────┬──┴─────┬─────┴──────────
 　│　　螣蛇　　　 │　　太陰　　　 │　　六合　　　 │
 　│　　休門　　天乙│　　死門　　天英│　　傷門　　天柱│
 　│　　天蓬　　坎一│　　天芮　　坤二│　　天沖　　震三│
 辰├───────────┼───────────┼───────────┤酉
 勾│　　白虎　　　 │　　　　　　 │　　玄武　　　 │陳
 陳│　　杜門　　天沖│　　　　　戊  │　　開門　　天任│武
 　│　　天輔　　巽四│　　　　　　 │　　天心　　乾六│
 　├───────────┼───────────┼───────────┤
 　│　　朱雀　　　 │　　九地　　　 │　　九天　　　 │
 卯│　　景門　　天任│　　生門　　天柱│　　驚門　　天芮│戌
 　│　　天英　　離九│　　天心　　兌七│　　天蓬　　艮八│
 ／─────────┬──┴─────┬─────┴──┬────────＼
／  寅　　　 │  丑　　 │  子　　 │  　 亥　　 ＼
```

---

## 📦 의존 패키지 · Dependencies

- [`sxtwl`](https://pypi.org/project/sxtwl/) — 중국 음력/절기 계산 · Chinese lunar calendar & solar terms
- [`kinliuren`](https://pypi.org/project/kinliuren/) — 대육임(大六壬) 포국 · Da Liu Ren divination
- [`streamlit`](https://streamlit.io/) — Web 인터랙티브 인터페이스 · Web UI framework
- [`pendulum`](https://pendulum.eustace.io/) — 시간대(timezone) 처리 · Timezone handling

---

## 🌐 온라인 포국 · Web App

설치 없이 브라우저에서 바로 기문 포국을 체험할 수 있습니다:

**Try it instantly in your browser — no installation needed:**

👉 **[https://kinqimen.streamlitapp.com](https://kinqimen.streamlitapp.com)**

---

## 🐛 이슈 · Issues

[GitHub Issues](https://github.com/kentang2017/kinqimen/issues)

---

## 📄 라이선스 · License

[MIT License](LICENSE)
