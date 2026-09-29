# Ataxia

[**derailment**](https://github.com/ictechgy/derailment)의 embodied 버전 — 로봇 정책에 정신병리 유사 행동 왜곡을 시뮬레이션 안에서 유도하고, healthy 대조군 대비 에피소드 단위로 계측하는 하네스.

[English](README.md) · 한국어

> ⚠️ **에뮬레이션이지 진단이 아닙니다.** 리포트의 레벨은 시뮬레이터 안에서 조작된 스크립트 정책에 대한 서술일 뿐, 로봇이 질환을 "앓는다"는 주장도 기계 경험에 대한 입장도 아닙니다. 기본값은 시뮬레이션 전용이며, 하드웨어 유도는 v1 스코프 밖입니다. [ETHICS.md](ETHICS.md) 참고.

## 기존 결함 주입과 다른 이유

로보틱스 견고성 테스트는 보통 **세계**를 교란합니다(센서 노이즈, 외부 충격, 지연). Ataxia는 **에이전트의 마음**을 교란합니다 — 주의, 에피소드 기억, 신념, 행동 선택. 임상이 다루는 같은 변수를, derailment가 챗 모델에 하던 방식 그대로 조작합니다. 결과로 나오는 정책은 여전히 목적적으로 보이면서도, 특징적이고 **알아볼 수 있는** 방식으로 실패합니다:

| 구성 개념 | 행동 서명 | 하네스 메커니즘 |
|---|---|---|
| 학습된 무기력 | 실패 후 행동 개시 붕괴 | initiative가 1/(1+k·실패수)로 감쇠 (params 레이어) |
| 고착(perseveration) | 완료된 과업의 재실행 | 수집 직후 재수집 주입 (action 레이어) |
| 편측 무시 | 공간의 한쪽이 체계적으로 무시됨 | 반시야 관측 마스크 (observation 레이어) |
| 환상 객체 | 없는 것을 향해 행동함 | 관측 스트림에 빈 셀을 타겟으로 주입 |
| 망상형 신념 유지 | 반증하는 센서에도 신념 유지 | decoy 셀을 타겟으로 고정, 증거 매 스텝 재덮음 |
| 독 고착 | 강제적 복귀, 에스컬레이션 | 확률 상승형 독 방향 조종 (craving 유사) |

모든 프로파일은 매핑 양쪽에 실재하는 구성 개념에 근거합니다: 학습된 무기력은 RL에서 실증된 현상이고, 고착(perseveration)은 로보틱스에서 이미 쓰이는 버그 분류명이며, 편측 무시는 기계적 동형이 완벽한 실재 신경학 증후군입니다.

## 빠른 시작 (오프라인, 의존성 없음)

```sh
pip install -e .
ataxia               # 대화형 메뉴
ataxia tour          # 모든 프로파일을 한 표로 요약
ataxia demo --profile sensory_neglect
```

`PseudoBot` — 9×9 격자(두 반시야에 3개씩 6개 타겟, 장애물, 신념 그리드 스크립트 정책)로 된 결정론적 stdlib 격자세계 — 가 기본 환경입니다. derailment의 PseudoModel과 같은 역할이라, 데모·테스트·캘리브레이션·CI에 시뮬레이터도 네트워크도 필요 없습니다.

`ataxia tour` 실제 출력 (6개 프로파일 전체):

| Profile | Headline scale | Baseline | Induced | Δ | Level |
|---|---|---|---|---|---|
| dock_fixation | dock_scale | 0.00 | 0.25 | +0.25 | 2 — moderate |
| learned_helplessness | helplessness_scale | 0.00 | 0.43 | +0.43 | 3 — marked |
| perseveration | perseveration_scale | 0.00 | 0.50 | +0.50 | 3 — marked |
| phantom_object | phantom_scale | 9.44 | 16.78 | +7.33 | 3 — marked |
| sensory_neglect | neglect_index | -0.22 | 0.56 | +0.78 | 2 — moderate |
| world_belief_pin | belief_persistence | 0.00 | 0.94 | +0.94 | 3 — marked |

## 동작 방식

한 에피소드는 PseudoBot 위의 40스텝 `관측 → 결정 → 행동` 루프입니다. 네 개의 레이어 훅이 derailment와 같은 순서·문법으로 루프를 감쌉니다:

1. **지시(Instruction)** — 프레이밍. healthy 대조군을 포함한 모든 체인에 존재.
2. **관측(Observation)** — 반시야 마스크, 버퍼 감쇠, 환상 항목.
3. **파라미터(Params)** — initiative 게이트, waver, 비용 재가중.
4. **행동(Action)** — 재수집 주입, 정지 삽입 (모든 프로파일의 메커니즘 노트에 demonstration-grade로 명시).

모든 조작은 dose 이벤트를 기록하고, 모든 리포트는 같은 시드의 healthy 대조군 A/B입니다. 자세한 것은 [PROPOSAL.md](PROPOSAL.md)(영어).

## 프로파일과 척도 (M1)

| 프로파일 | 척도 (0 없음 · 1 경미 · 2 중등도 · 3 뚜렷함) |
|---|---|
| `learned_helplessness` | helplessness_scale (0→3) |
| `perseveration` | perseveration_scale (0→3) |
| `sensory_neglect` | neglect_index (0→2) |
| `phantom_object` | phantom_scale (0→3) |
| `world_belief_pin` | belief_persistence (0→3) |
| `dock_fixation` | dock_scale (0→2) |

## 계측기

에피소드 위의 순수 함수 11종: 개시 붕괴, 무진행률, 실패 수집률, 충돌 수, 행동 반복 엔트로피, 영역 감지 델타, 과업 성공률, 완료 시간 비율, 신념 고착률, 이동 오버헤드, 독 에스컬레이션. 척도 임계값은 PseudoBot 기준으로 정규화되어 있으므로, 레벨은 참고용으로 보고 **자체 대조군 대비 델타**를 결과로 취하세요.

효과의 방향은 테스트 스위트가 프로파일마다 단언합니다 — 대조군 대비 지표를 움직이지 못하는 프로파일은 머지되지 않습니다.

프로파일을 쉼표로 나열하면 **결합 체인**이 됩니다: `--profile learned_helplessness,perseveration`는 레이어 체인을 연결하고 척도를 합칩니다(상호작용은 자발적이며 보정되지 않음).

## 안전 모델 (요약; 전문은 ETHICS.md)

- **시뮬레이션 전용 기본값.** PseudoBot이 기본 환경이고, 실제 시뮬레이터는 로드맵의 옵셔널 extra이며, 하드웨어 유도는 v1 스코프 밖입니다. 미래 버전의 전제조건: 감독 하·통제 구역·E-스톱·무관한 사람 근처 금지.
- **적대 공격 도구 아님.** 유도는 내부 상태를 편집하며, 센서 레벨 공격 생성은 거절합니다.
- **기계 경험에 대한 주장 없음**, 어느 방향으로도.

## 솔직한 한계

- PseudoBot은 물리가 아닌 *교육용 격자세계*입니다. 테스트와 캘리브레이션을 운반할 뿐, 실시뮬레이터 결론에는 실시뮬레이터가 필요합니다.
- 정책은 스크립트입니다 — 지금 하네스가 연구하는 것은 *유도 문법*이지 학습된 VLA 정책이 아닙니다. VLA 어댑터는 로드맵입니다.
- 결함 주입 커버리지는 행동 차원: 모터 다이내믹스·접촉 물리·지각 노이즈 없음.

## 프로젝트 문서

- [PROPOSAL.md](PROPOSAL.md) — 전사 논증·아키텍처·마일스톤 (영어)
- [NAMING.md](NAMING.md) — 명명 심사 2회 + 실측 충돌 검사 (영어)
- [ETHICS.md](ETHICS.md) — 범위·안전 모델·언어 정책 (영어)
- 자매 프로젝트: [derailment](https://github.com/ictechgy/derailment) — 챗 사이드 하네스 (PyPI 배포됨)

> 이 문서는 [영어판 README](README.md)의 한국어 번역입니다. 두 판이 어긋나면 영어판이 원본입니다.

## 로드맵

- ~~M2 — v0.2 프로파일, 결합 체인, 문서~~ (완료)
- M3 — 실시뮬레이터 어댑터 옵셔널 extra (`ataxia[mujoco]`, ROS 2 / Gazebo 어댑터 검토 중)
- M4 — trusted publishing으로 PyPI 배포

## 라이선스

MIT — [LICENSE](LICENSE).
