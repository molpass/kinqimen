# 堅奇門 · KinQiMen

Python 기문둔갑(奇門遁甲) 포국 시스템

> 이 저장소는 molpass가 포크한 사본입니다. 원문(중국어·영어)은 [README.en.md](./README.en.md)를 참고하세요.

온라인 포국: [kinqimen.streamlitapp.com](https://kinqimen.streamlitapp.com)

---

## 도입

기문둔갑(奇門遁甲)은 대육임(大六壬), 태을신수(太乙神數)와 더불어 **중국 3대 신비 예측술**로 불리며, 역대로 천자 곁의 국사(國師)와 군사(軍師)만이 익힐 수 있었습니다.

기문둔갑은 중국 고대에서 가장 심오한 예측학 중 하나입니다. 낙서구궁(洛書九宮)을 반(盤)으로 삼고, 음양오행·팔괘·천간지지·24절기를 결합하여 시공간이 회전하는 우주 에너지 매트릭스를 구성합니다. 전체 반에는 총 **1,080종의 국(局)**이 있어 매 시진마다 바뀌며, 천·지·인 삼재(三才)의 기운을 정밀하게 포착합니다. 의사결정, 방위, 사업, 그리고 개인의 길흉을 좇고 피하는 데 널리 활용됩니다.

---

## 기능 특징

| 기능 | 설명 |
|---|---|
| 시가기문(時家奇門) | 시진으로 기반(起盤)하는, 가장 흔히 쓰이는 전통 포국 방식 |
| 각가기문(刻家奇門) | 분 단위로 정밀 계산, 정확한 예측에 적합 |
| 금함옥경(金函玉鏡) | 금함 일가기문(日家奇門), 고전 일가 포국 |
| 탁보 / 치윤(拆補 / 置閏) | 탁보법과 치윤법을 모두 지원하여 각 유파에 유연 대응 |
| Web 포국 인터페이스 | Streamlit 기반 인터랙티브 온라인 포국 |
| 순수 Python | 가볍고 쓰기 쉬워 어떤 Python 프로젝트에도 임베드 가능 |

---

## 설치

```bash
pip install sxtwl
pip install kinqimen
```

---

## 빠른 시작

```python
from kinqimen import kinqimen

year, month, day, hour, minute = 2024, 6, 15, 14, 30

# 시가기문(탁보법)
result = kinqimen.Qimen(year, month, day, hour, minute).pan(1)   # 1=탁보, 2=치윤

# 각가기문(치윤법)
result = kinqimen.Qimen(year, month, day, hour, minute).pan_minute(2)

# 금함옥경 일가기문
result = kinqimen.Qimen(year, month, day, hour, minute).gpan()

# 종합 포국(시가 + 금함)
result = kinqimen.Qimen(year, month, day, hour, minute).overall()
```

---

## 포국 예시

다음은 기문 포국 결과 예시입니다(전통 표기 그대로):

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

## 의존 패키지

- [`sxtwl`](https://pypi.org/project/sxtwl/) — 중국 음력/절기 계산
- [`kinliuren`](https://pypi.org/project/kinliuren/) — 대육임(大六壬) 포국
- [`streamlit`](https://streamlit.io/) — Web 인터랙티브 인터페이스
- [`pendulum`](https://pendulum.eustace.io/) — 시간대 처리

---

## 온라인 포국

설치 없이 브라우저에서 바로 기문 포국을 체험할 수 있습니다: [kinqimen.streamlitapp.com](https://kinqimen.streamlitapp.com)

---

## 이슈

[GitHub Issues](https://github.com/kentang2017/kinqimen/issues)

---

## 라이선스

[MIT License](LICENSE)
