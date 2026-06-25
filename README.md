[README.md](https://github.com/user-attachments/files/29329159/README.md)
# 3D 폭죽 설치 게임

Python + Pygame + OpenGL 기반의 3D 폭죽 시뮬레이션 게임입니다.  
발사대를 배치하고 타임라인으로 폭죽 시퀀스를 연출할 수 있습니다.

## 설치

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate
```

## 실행

```bash
python "fireworks-맥북프로-2.py"
```

## 조작법

| 키 | 기능 |
|---|---|
| `1` / `Q` | 카메라 모드 — 드래그 회전 / 스크롤 줌 |
| `2` / `W` | 폭죽 배치 — 지면 클릭으로 발사대 설치 |
| `3` / `E` | 구조물 배치 — 건물·기둥 등 설치 |
| `4` / `R` | 선택 모드 — 배치 아이템 클릭 후 속성 수정 |
| `Enter` | 발사 시퀀스 시작 / 정지 |
| `F5` | 전체 초기화 |
| `ESC` | 종료 |

### 선택 모드 단축키

| 키 | 기능 |
|---|---|
| `←` / `→` | 발사 지연 ±0.5초 |
| `T` | 폭죽 모양 변경 |
| `P` | 색상 팔레트 변경 |
| `[` / `]` | 구조물 크기 조절 |
| `Del` | 선택 항목 삭제 |

## 폭죽 종류 (50+)

| 카테고리 | 종류 |
|---|---|
| 구형 개화 | Peony, Chrysanthemum, Dahlia, Pistil, Taisho, Pastel |
| 특수 별 효과 | Strobe, Glitter, Silver Rain, Kamuro, Senko |
| 형태 셸 | Ring, Double Ring, Saturn, Crossette, Star Mine, Heart, Butterfly |
| 꼬리 / 드리프트 | Willow, Brocade, Palm, Comet, Spider, Jellyfish |
| 낙하 / 폭포 | Niagara, Falling Leaves, Mine, Mine Fan, Mine Color, Mine Spiral, Mine Crackle, Mine Dragon, Mine Titan, Mine Rain, Mine Flower, Meteor |
| 다중 파열 | Bouquet, Rapid Fire, Cluster, Comet Shower, Fish |
| 기타 | Fountain |

## 배경 테마

낮 (Roblox), 밤하늘, 석양, 새벽, 우주, 설원, 사막

## 색상 팔레트

Red Gold, Blue & White, Green Lime, Pink Purple, Gold, Cyan, White

## 구조물

빌딩, 기둥, 피라미드, 아치, 플랫폼

## 지형 재질

잔디, 눈, 모래, 흙, 콘크리트, 용암
