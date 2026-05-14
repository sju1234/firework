"""
3D 폭죽 설치 게임
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1 / Q : 카메라 모드   드래그 회전 / 스크롤 줌
2 / W : 폭죽 배치     지면 클릭으로 발사대 설치
3 / E : 구조물 배치   지면 클릭으로 건물·기둥 등 설치
4 / R_key : 선택 모드 배치 아이템 클릭 → 속성 수정
  ├ ←/→  : 발사 지연 ±0.5초
  ├ T     : 폭죽 모양 변경
  ├ P     : 색상 팔레트 변경
  ├ [/]  : 구조물 크기 조절
  └ Del   : 삭제

Enter : 발사 시퀀스 시작 / 정지
F5    : 전체 초기화
ESC   : 종료
"""

import pygame
from pygame.locals import *
try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ModuleNotFoundError as e:
    raise SystemExit(
        "PyOpenGL 모듈이 설치되어 있지 않습니다.\n" \
        "터미널에서 다음을 실행하세요: pip install PyOpenGL PyOpenGL_accelerate"
    ) from e
import random, math, time, base64, json

# ── 설정 ──────────────────────────────────────────────────────────────────────
W, H      = 1280, 720
FPS       = 60
GRAVITY   = -0.04
GROUND_Y  = -30.0
MAX_PART  = 50000

MODE_CAM = 0; MODE_FW = 1; MODE_ST = 2; MODE_SEL = 3; MODE_TERRAIN = 4
MODE_LABEL = ["카메라 모드", "폭죽 배치", "구조물 배치", "선택 / 수정", "지형 편집"]

TILE           = 4.0                     # 지형 타일 크기 (월드 유닛)
TER_TOOLS      = ['raise','lower','flatten','smooth']
TER_TOOL_NAMES = ['올리기','내리기','평탄화','매끄럽게']

# ── DAW 타임라인 레이아웃 상수 ─────────────────────────────────────────────────
TL_H         = 280    # 타임라인 패널 전체 높이
TL_PICK_W    = 272    # 왼쪽 picker 영역 너비
TL_TRANSPORT = 36     # transport 행 높이
TL_RULER_H   = 22     # 눈금자 높이
CLIP_W       = 64     # 클립 기본 너비 (px)

PALETTES = [
    [(1.0,0.3,0.1),(1.0,0.6,0.0),(1.0,1.0,0.2)],
    [(0.2,0.5,1.0),(0.5,0.8,1.0),(1.0,1.0,1.0)],
    [(0.2,1.0,0.3),(0.8,1.0,0.2),(1.0,1.0,0.5)],
    [(1.0,0.2,0.8),(0.8,0.2,1.0),(1.0,0.6,1.0)],
    [(1.0,0.6,0.0),(1.0,0.9,0.1),(1.0,0.4,0.0)],
    [(0.3,1.0,1.0),(0.0,0.8,0.8),(1.0,1.0,1.0)],
    [(1.0,1.0,1.0),(0.9,0.9,0.8),(0.8,0.9,1.0)],
]
PAL_NAMES   = ["Red Gold","Blue & White","Green Lime","Pink Purple","Gold","Cyan","White"]

# ── 배경 테마 ──────────────────────────────────────────────────────────────────
# sky_top/sky_bot: 하늘 그라디언트 (RGB 0~1)
# ground: 지면 색  grid/grid2: 격자 색
# stars: 별 개수  fog: 안개 여부
BACKGROUNDS = [
    {
        'name': '낮 (Roblox)',
        'sky_top': (0.35, 0.52, 0.78), 'sky_bot': (0.70, 0.82, 0.95),
        'ground': (0.29, 0.55, 0.18), 'grid': (0.20, 0.42, 0.10), 'grid2': (0.15, 0.33, 0.08),
        'stars': 0,
    },
    {
        'name': '밤하늘',
        'sky_top': (0.01, 0.01, 0.06), 'sky_bot': (0.04, 0.04, 0.14),
        'ground': (0.08, 0.14, 0.08), 'grid': (0.10, 0.18, 0.10), 'grid2': (0.07, 0.12, 0.07),
        'stars': 300,
    },
    {
        'name': '석양',
        'sky_top': (0.08, 0.06, 0.18), 'sky_bot': (0.95, 0.40, 0.10),
        'ground': (0.25, 0.18, 0.12), 'grid': (0.32, 0.22, 0.12), 'grid2': (0.20, 0.14, 0.08),
        'stars': 60,
    },
    {
        'name': '새벽',
        'sky_top': (0.10, 0.05, 0.20), 'sky_bot': (0.80, 0.55, 0.75),
        'ground': (0.18, 0.15, 0.22), 'grid': (0.24, 0.18, 0.28), 'grid2': (0.14, 0.10, 0.18),
        'stars': 120,
    },
    {
        'name': '우주',
        'sky_top': (0.0, 0.0, 0.0), 'sky_bot': (0.0, 0.01, 0.05),
        'ground': (0.10, 0.10, 0.12), 'grid': (0.16, 0.16, 0.20), 'grid2': (0.10, 0.10, 0.14),
        'stars': 600,
    },
    {
        'name': '설원',
        'sky_top': (0.55, 0.68, 0.82), 'sky_bot': (0.85, 0.90, 0.95),
        'ground': (0.88, 0.92, 0.96), 'grid': (0.72, 0.78, 0.86), 'grid2': (0.60, 0.68, 0.78),
        'stars': 0,
    },
    {
        'name': '사막',
        'sky_top': (0.55, 0.72, 0.95), 'sky_bot': (0.95, 0.88, 0.65),
        'ground': (0.80, 0.65, 0.35), 'grid': (0.68, 0.52, 0.24), 'grid2': (0.56, 0.42, 0.18),
        'stars': 0,
    },
]
BG_NAMES = [b['name'] for b in BACKGROUNDS]

ENV_PANEL_W = 310   # 환경 설정 패널 너비
FW_PANEL_W  = 280   # 폭죽 커스텀 패널 너비

TERRAIN_MATERIALS = [
    {'name': '잔디',      'ground':(0.29,0.55,0.18),'grid':(0.20,0.42,0.10),'grid2':(0.15,0.33,0.08)},
    {'name': '눈',        'ground':(0.88,0.92,0.96),'grid':(0.72,0.78,0.86),'grid2':(0.60,0.68,0.78)},
    {'name': '모래',      'ground':(0.80,0.65,0.35),'grid':(0.68,0.52,0.24),'grid2':(0.56,0.42,0.18)},
    {'name': '흙',        'ground':(0.45,0.30,0.18),'grid':(0.35,0.22,0.12),'grid2':(0.28,0.18,0.09)},
    {'name': '콘크리트',  'ground':(0.55,0.56,0.57),'grid':(0.44,0.45,0.46),'grid2':(0.35,0.36,0.37)},
    {'name': '용암',      'ground':(0.18,0.05,0.02),'grid':(0.80,0.15,0.00),'grid2':(0.50,0.08,0.00)},
]

SHAPES = [
    # ── 구형 개화 셸 (Spherical Break Shells) ─────────────────────────────────
    'peony',         # Peony          — 구형 단색 개화, 무꼬리 별
    'chrysanthemum', # Chrysanthemum  — 긴 꼬리별 구형 개화
    'dahlia',        # Dahlia         — 굵은 꽃잎형 별 개화
    'pistil',        # Pistil         — 내외 2색 이중 구각
    'taisho',        # Taisho         — 균일 구형 피보나치 별 배열 (大正)
    'pastel',        # Pastel         — 저채도 소프트 구형 개화
    # ── 특수 별 효과 셸 (Special Star Effect Shells) ─────────────────────────
    'strobe',        # Strobe         — 명멸(明滅) 섬광 별
    'glitter_burst', # Glitter        — 황금 글리터 강하 별
    'silver_rain',   # Silver Rain    — 은색 빗줄기 낙하 별
    'kamuro',        # Kamuro         — 황금 폭포 낙하 (일본 전통, 金鵄)
    'senko',         # Senko          — 세선 금색 방사 (千光)
    # ── 형태 셸 (Shape Shells) ────────────────────────────────────────────────
    'ring',          # Ring           — 수평 원형 링
    'double_ring',   # Double Ring    — 기울어진 교차 2중 링
    'saturn',        # Saturn         — 구체 + 기울어진 적도 링
    'crossette',     # Crossette      — 방사 후 십자 분열 별
    'star',          # Star Mine      — 다각 방사형 스타
    'heart',         # Heart          — 하트 형태 셸
    'butterfly',     # Butterfly      — 나비 형태 셸
    # ── 꼬리 / 드리프트 셸 (Trail & Drift Shells) ────────────────────────────
    'willow',        # Willow         — 버드나무 드리핑 긴 꼬리
    'brocade',       # Brocade        — 황금 자수처럼 하늘 전체를 덮는 금색 폭포
    'palm',          # Palm           — 야자수형 굵은 방사 꼬리
    'comet',         # Comet          — 방향성 단일 혜성 꼬리
    'spider',        # Spider         — 방사 다리 + 늘어지는 은색 실
    'jellyfish',     # Jellyfish      — 반구 돔 + 드리핑 촉수
    # ── 낙하 / 폭포 효과 (Falling & Cascade Effects) ─────────────────────────
    'waterfall_fw',  # Niagara        — 나이아가라 폭포 은색 커튼
    'falling_leaves',# Falling Leaves — 나뭇잎이 흔들리며 하강하는 서정적 효과
    'mine',          # Mine           — 부채꼴 상향 발산 (지상 마인 효과)
    'mine_fan',      # Mine Fan       — 넓은 60° 부채꼴 팔레트 마인
    'mine_color',    # Mine Color     — 팔레트 색상 구역별 분리 마인
    'mine_spiral',   # Mine Spiral    — 나선형 상승 마인
    'mine_crackle',  # Mine Crackle   — 지직거리는 은백색 크래클 마인
    'mine_dragon',   # Mine Dragon    — 적금색 와이드 콘 드래곤 마인
    'mine_titan',    # Mine Titan     — 초대형 전방위 폭발 마인
    'mine_rain',     # Mine Rain      — 수직 상승 후 비처럼 낙하하는 마인
    'mine_flower',   # Mine Flower    — 꽃잎 형태로 퍼지는 마인
    'meteor',        # Meteor         — 다방향 강하 유성 꼬리
    # ── 다중 파열 셸 (Multi-Break Shells) ────────────────────────────────────
    'bouquet',       # Bouquet        — 공간 분산 미니 구형 다중 파열
    'rapid_fire',    # Rapid Fire     — 연속 순간 파열 (연발)
    'cluster_bomb',  # Cluster        — 자탄 분산 2차 파열
    'comet_shower',  # Comet Shower   — 방사형 다중 혜성 동시 발사
    'fish',          # Fish           — 물고기 유영 자율 이동 2단계 파티클
    # ── 기타 공인 효과 (Other Recognized Effects) ────────────────────────────
    'fountain',      # Fountain       — 포물선 아치 분수 효과
]
SHAPE_NAMES = [
    # 구형 개화 (Spherical Break)
    'Peony',        'Chrysanthemum', 'Dahlia',       'Pistil',       'Taisho',
    'Pastel',
    # 특수 별 효과 (Special Star Effects)
    'Strobe',       'Glitter',       'Silver Rain',  'Kamuro',       'Senko',
    # 형태 셸 (Shape Shells)
    'Ring',         'Double Ring',   'Saturn',       'Crossette',    'Star Mine',
    'Heart',        'Butterfly',
    # 꼬리 / 드리프트 (Trail & Drift)
    'Willow',       'Brocade',       'Palm',         'Comet',        'Spider',       'Jellyfish',
    # 낙하 / 폭포 (Falling & Cascade)
    'Niagara',      'Falling Leaves','Mine',
    'Mine Fan',     'Mine Color',    'Mine Spiral',  'Mine Crackle',
    'Mine Dragon',  'Mine Titan',    'Mine Rain',    'Mine Flower',
    'Meteor',
    # 다중 파열 (Multi-Break)
    'Bouquet',      'Rapid Fire',    'Cluster',      'Comet Shower',
    'Fish',
    # 기타 공인 효과 (Other)
    'Fountain',
]
ST_TYPES    = ['building','pillar','pyramid','arch','platform']
ST_NAMES    = ['빌딩','기둥','피라미드','아치','플랫폼']

# ── 케이크 연발 폭죽 ─────────────────────────────────────────────────────────
CAKE_DIR_NAMES = ['직상형','부채형','V형','지그재그','크로스형','웨이브형','역부채형']
CAKE_SPD_NAMES = ['단발템포','연사형','램핑','브레이크','피날레']

def _cake_build_rect(cx, cz, rows, cols, spacing, dir_angle_deg):
    """네모 패턴: rows×cols 격자, dir_angle_deg 방향으로 회전
    반환: [(x, z, launch_angle_deg, launch_dir_deg), ...]  발사 순서: 행별 왼→오"""
    import math as _m
    a = _m.radians(dir_angle_deg)
    ca, sa = _m.cos(a), _m.sin(a)
    result = []
    for r in range(rows):
        for c in range(cols):
            lx = (c - (cols-1)/2) * spacing
            lz = (r - (rows-1)/2) * spacing
            wx = cx + lx*ca - lz*sa
            wz = cz + lx*sa + lz*ca
            result.append((wx, wz, 0.0, 0.0))   # 직상 발사
    return result

def _cake_build_fan(cx, cz, n, fan_deg, dir_angle_deg, radius, tilt_deg):
    """부채꼴 패턴: n발을 fan_deg 각도 범위로 펼침
    반환: [(x, z, launch_angle_deg, launch_dir_deg), ...]"""
    import math as _m
    result = []
    for i in range(n):
        t = i / (n-1) if n > 1 else 0.5
        shot_angle_deg = dir_angle_deg + (t - 0.5) * fan_deg
        a = _m.radians(shot_angle_deg)
        wx = cx + _m.cos(a) * radius * 0.25
        wz = cz + _m.sin(a) * radius * 0.25
        # 각 발사체의 기울기: 중앙=tilt, 양끝=tilt (방향만 다름)
        launch_dir = shot_angle_deg
        result.append((wx, wz, tilt_deg, launch_dir))
    return result

def _cake_delays(n, spd_pat):
    """케이크 n발 발사 지연 시간 목록 반환 (초)"""
    delays = []
    t = 0.0
    if spd_pat == 0:   # 단발템포
        for i in range(n): delays.append(i * 0.45)
    elif spd_pat == 1: # 연사형
        for i in range(n): delays.append(i * 0.09)
    elif spd_pat == 2: # 램핑
        dt = 0.60
        for i in range(n):
            delays.append(t); t += max(0.07, dt); dt *= 0.78
    elif spd_pat == 3: # 브레이크 후 재가속
        a = max(1, n//3); b = max(1, n//3)
        for i in range(a):       delays.append(t); t += 0.10
        t += 0.70
        for i in range(b):       delays.append(t); t += 0.10
        t += 0.60
        for _ in range(n-a-b):   delays.append(t); t += 0.10
    else:              # 피날레 러시
        main = max(0, n - 4)
        for i in range(main):    delays.append(t); t += 0.38
        for _ in range(n-main):  delays.append(t); t += 0.06
    return delays

# ── GL 드로잉 헬퍼 ────────────────────────────────────────────────────────────
def _set_color(col, alpha=1.0):
    if len(col) == 3:
        glColor4f(col[0], col[1], col[2], alpha)
    else:
        glColor4f(*col)

def gl_box(cx, yb, cz, bw, bh, bd, col, alpha=1.0, wire=False):
    x0,x1 = cx-bw/2, cx+bw/2
    y0,y1 = yb, yb+bh
    z0,z1 = cz-bd/2, cz+bd/2
    faces = [
        [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
        [(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
        [(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
        [(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],
        [(x0,y1,z1),(x1,y1,z1),(x1,y1,z0),(x0,y1,z0)],
        [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
    ]
    prim = GL_LINE_LOOP if wire else GL_QUADS
    _set_color(col, alpha)
    for f in faces:
        glBegin(prim)
        for v in f: glVertex3f(*v)
        glEnd()

def gl_cylinder(cx, yb, cz, r, h, col, alpha=1.0, wire=False, segs=14):
    _set_color(col, alpha)
    glBegin(GL_LINE_STRIP if wire else GL_QUAD_STRIP)
    for i in range(segs+1):
        a = (i/segs)*2*math.pi
        glVertex3f(cx+r*math.cos(a), yb,   cz+r*math.sin(a))
        glVertex3f(cx+r*math.cos(a), yb+h, cz+r*math.sin(a))
    glEnd()
    for y in ([yb, yb+h] if not wire else [yb+h]):
        glBegin(GL_TRIANGLE_FAN if not wire else GL_LINE_LOOP)
        glVertex3f(cx, y, cz)
        for i in range(segs+1):
            a = (i/segs)*2*math.pi
            glVertex3f(cx+r*math.cos(a), y, cz+r*math.sin(a))
        glEnd()

def gl_pyramid(cx, yb, cz, base, height, col, alpha=1.0, wire=False):
    b = base/2
    tip = (cx, yb+height, cz)
    corners = [(cx-b,yb,cz-b),(cx+b,yb,cz-b),(cx+b,yb,cz+b),(cx-b,yb,cz+b)]
    _set_color(col, alpha)
    prim = GL_TRIANGLES if not wire else GL_LINE_LOOP
    for i in range(4):
        a,b2 = corners[i], corners[(i+1)%4]
        glBegin(prim)
        glVertex3f(*tip); glVertex3f(*a); glVertex3f(*b2)
        glEnd()
    glBegin(GL_QUADS if not wire else GL_LINE_LOOP)
    for c in corners: glVertex3f(*c)
    glEnd()

def gl_ground_ring(cx, cz, r, col, alpha=1.0, segs=32):
    _set_color(col, alpha)
    glBegin(GL_LINE_LOOP)
    for i in range(segs):
        a = (i/segs)*2*math.pi
        glVertex3f(cx+r*math.cos(a), GROUND_Y+0.05, cz+r*math.sin(a))
    glEnd()

# ── Particle ──────────────────────────────────────────────────────────────────
class Particle:
    # hot: 고온 지속 비율(0~1). 1.0 이면 전체 수명 내내 흰 고온 유지
    __slots__ = ['x','y','z','vx','vy','vz','r','g','b',
                 'life','max_life','size','drag','grav','hot','spark','strobe']

    def __init__(self, x,y,z, vx,vy,vz, color, life,
                 size=1.8, drag=0.978, grav=1.0, hot=0.25, spark=False, strobe=False):
        self.x,self.y,self.z = x,y,z
        self.vx,self.vy,self.vz = vx,vy,vz
        self.r,self.g,self.b = color
        self.life,self.max_life = life,life
        self.size   = size
        self.drag   = drag
        self.grav   = grav
        self.hot    = hot
        self.spark  = spark
        self.strobe = strobe  # True=마그네슘 스트로브 깜빡임

    def update(self):
        self.x += self.vx; self.y += self.vy; self.z += self.vz
        # 중력
        self.vy += GRAVITY * self.grav
        # 속도²에 비례하는 공기저항 근사 (선형 drag + 2차 보정)
        spd2 = self.vx*self.vx + self.vy*self.vy + self.vz*self.vz
        quad = 1.0 - (1.0 - self.drag) * (1.0 + spd2 * 0.012)
        quad = max(0.88, quad)
        self.vx *= quad; self.vy *= quad; self.vz *= quad
        self.life -= 1
        return self.life > 0 and self.y > GROUND_Y

    @property
    def alpha(self):
        a = self.life / self.max_life
        # 마지막 15% 수명에서 급격히 꺼짐 (빠른 소멸)
        if a < 0.15:
            return (a / 0.15) ** 1.6
        return a

    def hot_blend(self):
        """현재 수명 단계에 따른 색온도 보정값 (0=화학색, 1=흰 고온)"""
        a_raw = self.life / self.max_life
        if a_raw > (1.0 - self.hot):
            # 고온 구간: 흰색으로 블렌딩
            t = (a_raw - (1.0 - self.hot)) / self.hot
            return min(1.0, t * 1.2)
        return 0.0

# ── FishParticle ──────────────────────────────────────────────────────────────
class FishParticle(Particle):
    """물고기처럼 꿈틀거리는 자율 이동 파티클 (Fish 폭죽용)"""
    def __init__(self, x, y, z, vx, vy, vz, color, life, size=2.8, drag=0.960, grav=0.30):
        super().__init__(x, y, z, vx, vy, vz, color, life,
                         size=size, drag=drag, grav=grav, hot=0.18)
        self.ax = random.gauss(0, 0.040)
        self.ay = random.gauss(0, 0.018)
        self.az = random.gauss(0, 0.040)
        self.wobble_t  = random.randint(0, 3)
        self.spd_max   = random.uniform(0.70, 1.10)

    def update(self):
        # 2~4프레임마다 급격히 방향 전환 → 좁은 범위에서 빠르게 꿈틀
        self.wobble_t += 1
        if self.wobble_t >= random.randint(2, 4):
            self.wobble_t = 0
            self.ax += random.gauss(0, 0.075)
            self.ay += random.gauss(0, 0.035)
            self.az += random.gauss(0, 0.075)
            damp = 0.48  # 강한 감쇠로 좁은 반경 유지
            self.ax *= damp; self.ay *= damp; self.az *= damp
        self.vx += self.ax; self.vy += self.ay; self.vz += self.az
        self.vy += GRAVITY * self.grav
        spd2 = self.vx*self.vx + self.vy*self.vy + self.vz*self.vz
        if spd2 > self.spd_max * self.spd_max:
            s = self.spd_max / math.sqrt(spd2)
            self.vx *= s; self.vy *= s; self.vz *= s
        self.vx *= self.drag; self.vy *= self.drag; self.vz *= self.drag
        self.x += self.vx; self.y += self.vy; self.z += self.vz
        self.life -= 1
        return self.life > 0 and self.y > GROUND_Y

# ── LeafParticle ──────────────────────────────────────────────────────────────
class LeafParticle(Particle):
    """나뭇잎처럼 좌우로 흔들리며 낙하하는 파티클 (Falling Leaves용)"""
    def __init__(self, x, y, z, vy_init, color, life, size=2.8, grav=2.6):
        super().__init__(x, y, z, 0, vy_init, 0, color, life,
                         size=size, drag=0.997, grav=grav, hot=0.08)
        self.sway_angle = random.uniform(0, 2*math.pi)
        self.sway_phase = random.uniform(0, 2*math.pi)
        self.sway_speed = random.uniform(0.05, 0.13)
        self.sway_amp   = random.uniform(0.04, 0.11)

    def update(self):
        self.sway_phase += self.sway_speed
        self.vx = self.sway_amp * math.sin(self.sway_phase) * math.cos(self.sway_angle)
        self.vz = self.sway_amp * math.sin(self.sway_phase) * math.sin(self.sway_angle)
        self.vy += GRAVITY * self.grav
        self.vy *= self.drag
        self.x += self.vx; self.y += self.vy; self.z += self.vz
        self.life -= 1
        return self.life > 0 and self.y > GROUND_Y

# ── Rocket ────────────────────────────────────────────────────────────────────
class Rocket:
    def __init__(self, x, z, target_y, shape, palette):
        self.x,self.y,self.z = float(x), GROUND_Y, float(z)
        self.vy = random.uniform(1.6, 2.3)
        self.vx = random.uniform(-0.08, 0.08)
        self.vz = random.uniform(-0.08, 0.08)
        self.target_y = target_y
        self.shape = shape
        self.palette = palette
        self.trail = []
        # 커스텀 배율 (PlacedFirework.make_rockets()에서 설정)
        self.burst_size = 1.0
        self.part_mul   = 1.0
        self.grav_mul   = 1.0
        self.drag_mul   = 1.0
        # 모양 세부 파라미터
        self.spread     = 1.0   # 퍼짐 (속도 분산 폭)
        self.tail_len   = 1.0   # 꼬리 길이 (수명 배율)
        self.wobble     = 0.0   # 방향 흔들림 (0=정확, 2=난잡)
        self.secondary  = 1.0   # 보조 이펙트 강도
        self.arm_count  = 0     # 팔 수 (0=기본값 사용)
        self.lift       = 0.0   # 위 편향 (-1=아래, 2=강하게 위)

    def update(self):
        self.trail.append((self.x,self.y,self.z))
        if len(self.trail) > 28: self.trail.pop(0)
        self.x+=self.vx; self.y+=self.vy; self.z+=self.vz
        self.vy -= 0.025
        return self.y < self.target_y and self.vy > 0

    def explode(self):
        parts = []
        s  = self.shape
        pal = self.palette
        ox,oy,oz = self.x, self.y, self.z

        _bsz  = self.burst_size
        _gmul = self.grav_mul
        _dmul = self.drag_mul
        _spr  = max(0.05, self.spread)
        _tail = max(0.1,  self.tail_len)
        _wob  = self.wobble
        _sec  = max(0.0,  self.secondary)
        _arms = self.arm_count   # 0 = 기본값
        _lift = self.lift

        def p(vx,vy,vz, life, col=None, size=1.8, drag=0.978, grav=1.0, hot=0.12):
            c = col if col else random.choice(pal)
            # 퍼짐: 속도 크기에 분산 추가
            if abs(_spr - 1.0) > 0.05:
                factor = max(0.05, random.gauss(1.0, abs(_spr-1.0)*0.35))
                vx *= factor; vy *= factor; vz *= factor
            # 흔들림
            if _wob > 0.01:
                vx += random.gauss(0, _wob*0.07)
                vy += random.gauss(0, _wob*0.07)
                vz += random.gauss(0, _wob*0.07)
            # 위 편향
            vy += _lift * 0.35
            vx *= _bsz; vy *= _bsz; vz *= _bsz
            drag2 = max(0.80, min(0.999, 1.0 - (1.0-drag)*_dmul))
            life2 = max(3, int(life * _tail))
            # 고속 파티클은 더 오래 고온 유지
            spd = math.sqrt(vx*vx + vy*vy + vz*vz)
            hot2 = min(0.95, hot + spd * 0.018)
            parts.append(Particle(ox,oy,oz, vx,vy,vz, c, life2, size, drag2, grav*_gmul, hot2))

        def sphere_v(sp):
            theta = random.uniform(0, 2*math.pi)
            phi   = math.acos(random.uniform(-1, 1))
            return sp*math.sin(phi)*math.cos(theta), sp*math.sin(phi)*math.sin(theta), sp*math.cos(phi)

        def upper_v(sp, spread=1.0):
            theta = random.uniform(0, 2*math.pi)
            phi   = math.acos(random.uniform(0, 1))
            return sp*math.sin(phi)*math.cos(theta)*spread, sp*math.cos(phi), sp*math.sin(phi)*math.sin(theta)*spread

        def ring_v(sp, tilt=0.0, jitter=0.03):
            theta = random.uniform(0, 2*math.pi)
            vx = sp*math.cos(theta); vz = sp*math.sin(theta)
            vy = vx*tilt + random.gauss(0, jitter)
            return vx, vy, vz

        # ── 공통 이펙트 헬퍼 ─────────────────────────────────────────────────
        GOLD   = [(1.0,0.90,0.2),(1.0,0.75,0.0),(1.0,1.0,0.7),(1.0,0.95,0.4)]
        WHITE  = [(1.0,1.0,1.0),(0.95,0.98,1.0),(1.0,1.0,0.9)]

        def sparkle(n, speed=1.8):
            """황금/흰색 반짝이 — 고온 유지"""
            n = max(0, int(n * _sec))
            for _ in range(n):
                vx2,vy2,vz2 = sphere_v(random.uniform(0.2, speed))
                c2 = random.choice(GOLD+WHITE)
                p(vx2,vy2,vz2, random.randint(12,28), col=c2,
                  size=1.4, drag=0.960, grav=2.2, hot=0.55)

        def shock_ring(sp=1.6, n=60):
            """수평 충격파 링 — 순간 고온"""
            n = max(0, int(n * _sec))
            for i in range(n):
                theta2 = (i/n)*2*math.pi + random.gauss(0,0.05) if n else 0
                sv = random.gauss(sp, 0.06)
                p(sv*math.cos(theta2), random.gauss(0,0.02), sv*math.sin(theta2),
                  random.randint(10,18), col=random.choice(WHITE),
                  size=1.2, drag=0.968, grav=0.4, hot=0.80)

        def glitter_crown(n=80, sp_min=0.8, sp_max=2.2):
            """크라운 모양 빛줄기 — 글리터 황금"""
            n = max(0, int(n * _sec))
            for _ in range(n):
                phi2   = random.uniform(0, math.pi*0.45)
                theta2 = random.uniform(0, 2*math.pi)
                sp2    = random.uniform(sp_min, sp_max)
                vx2 = sp2*math.sin(phi2)*math.cos(theta2)
                vy2 = sp2*math.cos(phi2)
                vz2 = sp2*math.sin(phi2)*math.sin(theta2)
                p(vx2,vy2,vz2, random.randint(8,20), col=random.choice(GOLD),
                  size=1.3, drag=0.955, grav=3.0, hot=0.45)

        def streamer(theta2, n=30, spread=0.08):
            """단일 빛줄기 스트리머"""
            for k2 in range(n):
                sp2 = 0.15 + k2*0.045
                t2  = theta2 + random.gauss(0, spread)
                p(sp2*math.cos(t2), random.gauss(0,0.04), sp2*math.sin(t2),
                  random.randint(50,90), size=2.0, drag=0.974, hot=0.30)

        # ── 모란 (Peony) ──────────────────────────────────────────────────────
        if s == 'peony':
            # 균일한 구형 개화 — 깨끗하고 둥근 별 분포
            for _ in range(random.randint(380, 460)):
                sp = random.gauss(0.82, 0.10); sp = max(0.2, sp)
                vx,vy,vz = sphere_v(sp)
                p(vx,vy,vz, random.randint(65,95), drag=0.980, grav=0.75, size=2.2)
            for _ in range(55):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.25))
                p(vx,vy,vz, random.randint(30,55), size=3.0, drag=0.984)

        # ── 국화 (Chrysanthemum) ─────────────────────────────────────────────
        elif s == 'chrysanthemum':
            # 각 방향마다 4단 속도 파티클 → 방사형 꼬리 줄기 연출
            n_dir = random.randint(260, 340)
            for _ in range(n_dir):
                theta2 = random.uniform(0, 2*math.pi)
                phi2   = math.acos(random.uniform(-1, 1))
                base_sp = random.gauss(0.92, 0.10); base_sp = max(0.2, base_sp)
                ux = math.sin(phi2)*math.cos(theta2)
                uy = math.sin(phi2)*math.sin(theta2)
                uz = math.cos(phi2)
                for fac, sz, lf in [(1.00,2.4,115),(0.72,2.0,102),(0.48,1.6,88),(0.26,1.2,73)]:
                    p(ux*base_sp*fac, uy*base_sp*fac, uz*base_sp*fac,
                      random.randint(lf-8, lf+8), drag=0.974, grav=1.0, size=sz)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.25))
                p(vx,vy,vz, random.randint(30,55), size=3.2, drag=0.985)

        # ── 버드나무 (Willow) ────────────────────────────────────────────────
        elif s == 'willow':
            GOLD_W = [(1.0,0.90,0.20),(1.0,0.75,0.05),(1.0,1.0,0.65),(0.95,0.80,0.15)]
            # 전 방향 분출 후 강한 중력 → 처지는 버드나무 가지
            for _ in range(random.randint(420, 520)):
                theta2 = random.uniform(0, 2*math.pi)
                phi2   = math.acos(random.uniform(-1, 1))
                sp     = random.gauss(0.88, 0.12); sp = max(0.15, sp)
                vx = sp*math.sin(phi2)*math.cos(theta2)
                vy = sp*math.sin(phi2)*math.sin(theta2)
                vz = sp*math.cos(phi2)
                p(vx,vy,vz, random.randint(105,155), col=random.choice(GOLD_W),
                  drag=0.964, grav=4.0, size=1.8, hot=0.22)
            for _ in range(55):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.22))
                p(vx,vy,vz, random.randint(30,55), size=3.0, drag=0.985)

        # ── 카무로 (Kamuro) ──────────────────────────────────────────────────
        elif s == 'kamuro':
            GOLD_K = [(1.0,0.88,0.12),(1.0,0.72,0.0),(1.0,1.0,0.62),(0.9,0.7,0.0)]
            # 상반구 분출 + 극강 중력 → 황금 폭포 커튼 (철분/숯 hot=0.55)
            for _ in range(random.randint(500, 620)):
                vx,vy,vz = upper_v(random.uniform(0.35, 1.10))
                p(vx,vy,vz, random.randint(115,170),
                  col=random.choice(GOLD_K), drag=0.957, grav=4.8, size=2.2, hot=0.55)
            for _ in range(100):
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(0.08, 0.55)
                p(sp*math.cos(theta2), random.uniform(0.2,0.7), sp*math.sin(theta2),
                  random.randint(90,130), col=random.choice(GOLD_K),
                  drag=0.955, grav=5.2, size=1.8, hot=0.50)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.3))
                p(vx,vy,vz, random.randint(30,55), col=(1.0,1.0,0.8), size=3.2, drag=0.984, hot=0.70)

        # ── 브로케이드 (Brocade) ──────────────────────────────────────────────
        elif s == 'brocade':
            BROCADE = [(1.0,0.95,0.35),(1.0,0.82,0.10),(1.0,1.0,0.72),
                       (1.0,0.70,0.0),(0.95,0.88,0.22),(1.0,0.60,0.0)]
            # 외층: 빠르고 강한 중력 → 황금 자수가 쏟아지는 느낌
            for _ in range(random.randint(650, 800)):
                theta2 = random.uniform(0, 2*math.pi)
                phi2   = math.acos(random.uniform(-1, 1))
                sp = random.gauss(1.25, 0.22) * _bsz; sp = max(0.3, sp)
                vx = sp*math.sin(phi2)*math.cos(theta2)
                vy = sp*math.sin(phi2)*math.sin(theta2)
                vz = sp*math.cos(phi2)
                p(vx,vy,vz, random.randint(130,185),
                  col=random.choice(BROCADE), drag=0.958, grav=5.5, size=2.4, hot=0.62)
            # 내층: 느리고 조밀한 금빛 레이어
            for _ in range(220):
                theta2 = random.uniform(0, 2*math.pi)
                phi2   = math.acos(random.uniform(-1, 1))
                sp = random.gauss(0.55, 0.12) * _bsz; sp = max(0.1, sp)
                vx = sp*math.sin(phi2)*math.cos(theta2)
                vy = sp*math.sin(phi2)*math.sin(theta2)
                vz = sp*math.cos(phi2)
                p(vx,vy,vz, random.randint(105,150),
                  col=random.choice(BROCADE), drag=0.962, grav=4.8, size=1.8, hot=0.70)

        # ── 야자수 (Palm) ────────────────────────────────────────────────────
        elif s == 'palm':
            arms = _arms if _arms > 0 else random.randint(10, 14)
            for arm in range(arms):
                base_theta = (arm/arms)*2*math.pi
                n_per_arm  = random.randint(28, 40)
                for k2 in range(n_per_arm):
                    theta2 = base_theta + random.gauss(0, 0.08)
                    sp     = 0.10 + k2*0.055
                    vx = sp*math.cos(theta2)*0.72
                    vy = sp * random.uniform(0.45, 0.95)
                    vz = sp*math.sin(theta2)*0.72
                    grav2 = 1.8 + k2*0.12  # 끝으로 갈수록 처짐
                    p(vx,vy,vz, random.randint(75,115), drag=0.961, grav=grav2, size=2.4)
                for _ in range(10):
                    theta2 = base_theta + random.gauss(0, 0.20)
                    sp     = random.uniform(0.5, 1.1)
                    p(sp*math.cos(theta2)*0.6, random.uniform(-0.05, 0.25), sp*math.sin(theta2)*0.6,
                      random.randint(25,50), col=pal[-1], size=1.6, drag=0.966, grav=4.0)

        # ── 링 (Ring) ────────────────────────────────────────────────────────
        elif s == 'ring':
            cnt = random.randint(280, 360)
            for i in range(cnt):
                theta2 = (i/cnt)*2*math.pi
                sv = random.gauss(1.05, 0.028)
                p(sv*math.cos(theta2), random.gauss(0.0, 0.022), sv*math.sin(theta2),
                  random.randint(70,105), drag=0.983, grav=0.70, size=2.3)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 이중링 (Double Ring) ──────────────────────────────────────────────
        elif s == 'double_ring':
            configs = [(0.40, pal[0]), (-0.40, pal[-1]), (0.0, pal[1] if len(pal)>1 else pal[0])]
            for tilt, col2 in configs:
                cnt = random.randint(200, 250)
                for i in range(cnt):
                    theta2 = (i/cnt)*2*math.pi
                    sv = random.gauss(0.96, 0.028)
                    vx = sv*math.cos(theta2); vz = sv*math.sin(theta2)
                    vy = vx*tilt + random.gauss(0, 0.025)
                    p(vx,vy,vz, random.randint(72,108), col=col2,
                      drag=0.982, grav=0.80, size=2.0)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 달리아 (Dahlia) ───────────────────────────────────────────────────
        elif s == 'dahlia':
            arms = _arms if _arms > 0 else random.randint(10, 14)
            for arm in range(arms):
                theta2 = (arm/arms)*2*math.pi
                col_idx = arm % len(pal)
                cnt = random.randint(28, 40)
                for k2 in range(cnt):
                    sp   = k2*0.04 + 0.08
                    jit  = random.gauss(0, 0.05) if sp > 0.4 else random.gauss(0, 0.12)
                    vx   = sp*math.cos(theta2+jit)
                    vy   = sp*random.uniform(-0.10, 0.10)
                    vz   = sp*math.sin(theta2+jit)
                    p(vx,vy,vz, random.randint(65,100), col=pal[col_idx],
                      drag=0.977, grav=0.90, size=2.3)
                sp_tip = cnt*0.04 + 0.08
                for _ in range(14):
                    jit2 = random.gauss(0, 0.15)
                    vx   = sp_tip*math.cos(theta2+jit2)*random.uniform(0.85,1.15)
                    vz   = sp_tip*math.sin(theta2+jit2)*random.uniform(0.85,1.15)
                    p(vx, random.gauss(0,0.08), vz,
                      random.randint(20,38), col=pal[col_idx],
                      size=1.5, drag=0.968, grav=2.2)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 교차불꽃 (Crossette) ──────────────────────────────────────────────
        elif s == 'crossette':
            # 링 별이 날아가다 중간에 4방향으로 분열
            cnt = random.randint(60, 80)
            star_life = random.randint(22, 30)
            split_t   = int(star_life * 0.55)          # 분열 프레임
            d_ring    = 0.984
            geo       = (1.0 - d_ring**split_t) / (1.0 - d_ring)  # 이동거리 합산
            grav_drop = GRAVITY * _gmul * (split_t * (split_t - 1) / 2)
            sp_ring   = 0.90
            split_sp  = 0.68
            drag_spl  = max(0.80, min(0.999, 1.0 - (1.0-0.976)*_dmul))

            for i in range(cnt):
                ti = (i / cnt) * 2 * math.pi
                # 1차 링 별
                p(sp_ring*math.cos(ti), random.gauss(0.0, 0.035),
                  sp_ring*math.sin(ti), star_life + 5,
                  drag=d_ring, size=2.6, hot=0.40)
                # 분열 지점 (p()가 _bsz 곱하므로 동일하게 적용)
                vx0 = sp_ring * math.cos(ti) * _bsz
                vz0 = sp_ring * math.sin(ti) * _bsz
                sx = ox + vx0 * geo
                sy = oy + grav_drop
                sz = oz + vz0 * geo
                # 수직 단위벡터
                vn = max(1e-6, math.sqrt(vx0*vx0 + vz0*vz0))
                px = -vz0/vn;  pz = vx0/vn
                sp2 = split_sp * _bsz
                for dvx, dvy, dvz in [
                    ( px*sp2,       0.0,     pz*sp2),
                    (-px*sp2,       0.0,    -pz*sp2),
                    ( 0.0,    sp2*0.80,      0.0),
                    ( 0.0,   -sp2*0.55,      0.0),
                ]:
                    parts.append(Particle(sx, sy, sz, dvx, dvy, dvz,
                                          random.choice(pal),
                                          random.randint(55, 88),
                                          size=2.0, drag=drag_spl,
                                          grav=_gmul*1.2, hot=0.28))
            for _ in range(40):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(20,45), size=3.0, drag=0.985)

        # ── 암술형 (Pistil) ───────────────────────────────────────────────────
        elif s == 'pistil':
            # 내부 구체 (색1) + 외부 정밀 링 (색2) — 확실한 2층 구조
            for _ in range(200):
                vx,vy,vz = sphere_v(random.uniform(0.10, 0.48))
                p(vx,vy,vz, random.randint(50,80), col=pal[0], drag=0.977, grav=0.85, size=2.6)
            cnt = random.randint(280, 340)
            for i in range(cnt):
                theta2 = (i/cnt)*2*math.pi
                sv = random.gauss(1.15, 0.032)
                p(sv*math.cos(theta2), random.gauss(0,0.030), sv*math.sin(theta2),
                  random.randint(75,108),
                  col=pal[1] if len(pal)>1 else pal[0],
                  drag=0.983, grav=0.72, size=2.1)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 토성형 (Saturn) ───────────────────────────────────────────────────
        elif s == 'saturn':
            # 중심 구체 + 2개 기울어진 넓은 링
            for _ in range(280):
                sp = random.gauss(0.68, 0.12); sp = max(0.08, sp)
                vx,vy,vz = sphere_v(sp)
                p(vx,vy,vz, random.randint(60,95), drag=0.980, grav=0.80, size=2.1)
            for tilt in [0.50, -0.38]:
                cnt = random.randint(220, 270)
                for i in range(cnt):
                    theta2 = (i/cnt)*2*math.pi
                    sv = random.gauss(1.40, 0.028)
                    vx = sv*math.cos(theta2); vz = sv*math.sin(theta2)
                    vy = vx*tilt + random.gauss(0, 0.025)
                    p(vx,vy,vz, random.randint(80,115),
                      col=pal[1] if len(pal)>1 else pal[0],
                      drag=0.984, grav=0.72, size=2.1)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 스타마인 (Star Mine) ──────────────────────────────────────────────
        elif s == 'star':
            # 50개 구가 위로 솟구쳐 각자 정점 부근에서 아주 작게 터짐
            n_balls = random.randint(45, 55)
            for bi in range(n_balls):
                phi2   = math.acos(random.uniform(0.55, 1.00))  # 0~57° 상향 원뿔
                theta2 = random.uniform(0, 2*math.pi)
                sp_ball = random.gauss(1.20, 0.22); sp_ball = max(0.4, sp_ball)
                bvx = sp_ball * math.sin(phi2) * math.cos(theta2)
                bvy = sp_ball * math.cos(phi2)
                bvz = sp_ball * math.sin(phi2) * math.sin(theta2)
                col2 = pal[bi % len(pal)]
                # 공 본체 (밀집 클러스터)
                for _ in range(random.randint(6, 9)):
                    vx2 = bvx + random.gauss(0, 0.04)
                    vy2 = bvy + random.gauss(0, 0.04)
                    vz2 = bvz + random.gauss(0, 0.04)
                    p(vx2, vy2, vz2, random.randint(35, 52),
                      col=col2, drag=0.976, grav=2.0, size=2.4, hot=0.45)
                # 작은 burst (같은 방향 + 넓은 퍼짐 → 정점 부근 mini-explosion 효과)
                for _ in range(random.randint(12, 20)):
                    evx = bvx + random.gauss(0, 0.24)
                    evy = bvy + random.gauss(0, 0.24)
                    evz = bvz + random.gauss(0, 0.24)
                    p(evx, evy, evz, random.randint(18, 35),
                      col=col2, drag=0.966, grav=2.2, size=1.5, hot=0.32)

        # ── 하트 (Heart) ─────────────────────────────────────────────────────
        elif s == 'heart':
            cnt = random.randint(500, 620)
            for i in range(cnt):
                t2  = (i/cnt)*2*math.pi
                hx  = 16*(math.sin(t2)**3)
                hy  = 13*math.cos(t2)-5*math.cos(2*t2)-2*math.cos(3*t2)-math.cos(4*t2)
                sc  = random.uniform(0.040, 0.062)
                vx  = hx*sc + random.gauss(0, 0.025)
                vy  = hy*sc + random.gauss(0, 0.025)
                vz  = random.gauss(0, 0.08)
                p(vx,vy,vz, random.randint(75,115), drag=0.977, grav=0.70, size=2.3)
            for _ in range(120):
                t2  = random.uniform(0, 2*math.pi)
                hx  = 16*(math.sin(t2)**3)
                hy  = 13*math.cos(t2)-5*math.cos(2*t2)-2*math.cos(3*t2)-math.cos(4*t2)
                sc  = random.uniform(0.012, 0.038)
                vx  = hx*sc + random.gauss(0, 0.018)
                vy  = hy*sc + random.gauss(0, 0.018)
                vz  = random.gauss(0, 0.04)
                p(vx,vy,vz, random.randint(45,80), col=pal[0], size=2.8, drag=0.981, grav=0.70)

        # ── 부케 (Bouquet) ────────────────────────────────────────────────────
        elif s == 'bouquet':
            sub = random.randint(7, 10)
            for si in range(sub):
                offset_phi2   = math.acos(random.uniform(-0.20, 0.82))
                offset_theta2 = random.uniform(0, 2*math.pi)
                od  = random.uniform(1.0, 3.5)
                cx2 = ox + od*math.sin(offset_phi2)*math.cos(offset_theta2)
                cy2 = oy + od*math.cos(offset_phi2)
                cz2 = oz + od*math.sin(offset_phi2)*math.sin(offset_theta2)
                col2 = pal[si % len(pal)]
                for _ in range(random.randint(65, 90)):
                    sp2 = random.gauss(0.55, 0.12); sp2 = max(0.08, sp2)
                    vx2,vy2,vz2 = sphere_v(sp2)
                    parts.append(Particle(cx2,cy2,cz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          col2, random.randint(50,85),
                                          2.0, 0.978, 0.85*_gmul))
                for _ in range(12):
                    vx2,vy2,vz2 = sphere_v(random.uniform(0.4, 1.1))
                    parts.append(Particle(cx2,cy2,cz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          (1.0,1.0,0.92), random.randint(8,20),
                                          2.8, 0.968, 1.5*_gmul, 0.80))

        # ── 혜성꼬리 (Comet) ─────────────────────────────────────────────────
        elif s == 'comet':
            # 폭발 없음 — 정점에서 극소 고온 섬광만 (빛이 꺼지듯)
            for _ in range(random.randint(2, 4)):
                p(0.0, 0.0, 0.0, random.randint(3, 7),
                  col=(1.0, 1.0, 1.0), size=6.0, drag=0.995, grav=0.0, hot=1.0)

        # ── 스트로브 (Strobe) ─────────────────────────────────────────────────
        elif s == 'strobe':
            # 비행 중 trail이 주 효과 — 정점 도달 시 극소 섬광
            for _ in range(random.randint(8, 14)):
                vx,vy,vz = sphere_v(random.uniform(0.06, 0.25))
                life2 = max(3, int(random.randint(18,35) * _tail))
                parts.append(Particle(ox,oy,oz, vx*_bsz,vy*_bsz,vz*_bsz,
                                      (1.0,1.0,1.0), life2,
                                      size=3.0, drag=0.990, grav=0.2*_gmul,
                                      strobe=True))

        # ── 해파리 (Jellyfish) ────────────────────────────────────────────────
        elif s == 'jellyfish':
            # 돔 (상반구) — 가벼운 중력으로 둥실
            for _ in range(random.randint(280, 360)):
                vx,vy,vz = upper_v(random.gauss(0.80, 0.14), spread=1.0)
                p(vx,vy,vz, random.randint(55,90), drag=0.979, grav=0.50, size=2.0)
            # 촉수 — dome 가장자리서 아래로 늘어짐
            tentacles = _arms if _arms > 0 else random.randint(8, 12)
            for arm in range(tentacles):
                theta2 = (arm/tentacles)*2*math.pi + random.gauss(0, 0.12)
                dome_sp = random.uniform(0.55, 0.92)
                for k2 in range(random.randint(16, 24)):
                    vx2 = dome_sp*math.cos(theta2)*0.55
                    vy2 = -0.08 - k2*0.07 + random.gauss(0, 0.04)
                    vz2 = dome_sp*math.sin(theta2)*0.55
                    p(vx2, vy2, vz2, random.randint(75,115),
                      col=pal[arm%len(pal)], drag=0.964, grav=3.0, size=1.7)
            for _ in range(40):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.18))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 거미 (Spider) ─────────────────────────────────────────────────────
        elif s == 'spider':
            SILVER_S = [(0.88,0.92,1.0),(1.0,1.0,1.0),(0.78,0.84,0.94)]
            legs = _arms if _arms > 0 else random.randint(6, 9)
            for leg in range(legs):
                theta2  = (leg/legs)*2*math.pi
                col_leg = pal[leg % len(pal)]
                n_along = random.randint(20, 28)
                # 다리 몸통 — 방사형 증분
                for k2 in range(n_along):
                    sp = 0.08 + k2*0.06
                    vx = sp*math.cos(theta2) + random.gauss(0, 0.03)
                    vy = random.gauss(0.0, 0.04)
                    vz = sp*math.sin(theta2) + random.gauss(0, 0.03)
                    p(vx,vy,vz, random.randint(52,88), col=col_leg,
                      drag=0.977, grav=1.0, size=2.2)
                # 실 끝 — arm 방향 유지하되 극강 중력으로 낙하 (거미 다리 처짐)
                tip_sp = 0.08 + n_along*0.06
                for k3 in range(random.randint(18, 26)):
                    sp2 = tip_sp * random.uniform(0.90, 1.10)
                    vx  = sp2*math.cos(theta2) + random.gauss(0, 0.03)
                    vy  = -0.04 - k3*0.05 + random.gauss(0, 0.03)
                    vz  = sp2*math.sin(theta2) + random.gauss(0, 0.03)
                    p(vx, vy, vz, random.randint(65,100),
                      col=random.choice(SILVER_S), drag=0.960, grav=_gmul*3.8, size=1.4, hot=0.0)
            for _ in range(75):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.25))
                p(vx,vy,vz, random.randint(28,52), size=3.0, drag=0.983)

        # ── 연발 (Rapid Fire) ─────────────────────────────────────────────────
        elif s == 'rapid_fire':
            sub_cnt = random.randint(6, 10)
            for si in range(sub_cnt):
                svx,svy,svz = sphere_v(random.uniform(0.4, 1.2))
                sx = ox + svx*3.5; sy = oy + svy*2.5; sz2 = oz + svz*3.5
                col2 = pal[si % len(pal)]
                for _ in range(random.randint(55, 80)):
                    sp2 = random.gauss(0.72, 0.16); sp2 = max(0.1, sp2)
                    vx2,vy2,vz2 = sphere_v(sp2)
                    parts.append(Particle(sx,sy,sz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          col2, random.randint(45,80),
                                          2.0, 0.977, _gmul))
                for _ in range(10):
                    vx2,vy2,vz2 = sphere_v(random.uniform(0.3, 0.9))
                    parts.append(Particle(sx,sy,sz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          (1.0,1.0,0.92), random.randint(6,16),
                                          3.2, 0.965, _gmul, 0.80))

        # ── 타상연화 (Taisho) ─────────────────────────────────────────────────
        elif s == 'taisho':
            # 피보나치 나선 균등 구형 배열
            phi_g = (1+math.sqrt(5))/2
            n = random.randint(520, 660)
            for i in range(n):
                theta2 = 2*math.pi*i/phi_g
                phi2   = math.acos(1 - 2*(i+0.5)/n)
                sp     = random.gauss(1.02, 0.055)
                vx = sp*math.sin(phi2)*math.cos(theta2)
                vy = sp*math.cos(phi2)
                vz = sp*math.sin(phi2)*math.sin(theta2)
                c2 = pal[i % len(pal)]
                p(vx,vy,vz, random.randint(72,115), col=c2, drag=0.981, grav=0.82, size=2.1)
            for _ in range(55):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.22))
                p(vx,vy,vz, random.randint(28,55), size=3.0, drag=0.985)

        # ── 은비 (Silver Rain) ────────────────────────────────────────────────
        elif s == 'silver_rain':
            SILVER_R = [(0.85,0.88,0.92),(0.92,0.95,1.0),(1.0,1.0,1.0),(0.75,0.80,0.88)]
            # 넓은 수평 퍼짐 + 극강 중력 → 은빛 비처럼 수직 낙하
            for _ in range(random.randint(480, 580)):
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(0.25, 1.15)
                vx = sp*math.cos(theta2)
                vy = random.uniform(0.15, 0.85)
                vz = sp*math.sin(theta2)
                p(vx,vy,vz, random.randint(95,145), col=random.choice(SILVER_R),
                  drag=0.964, grav=5.0, size=1.8)
            for _ in range(60):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.4))
                p(vx,vy,vz, random.randint(22,48), col=(1.0,1.0,1.0), size=3.2, drag=0.982)

        # ── 금빛글리터 (Glitter Burst) ────────────────────────────────────────
        elif s == 'glitter_burst':
            GOLD_G = [(1.0,0.90,0.20),(1.0,0.75,0.05),(1.0,1.0,0.65),(0.95,0.80,0.15)]
            # 상반구 황금 글리터 분출
            for _ in range(random.randint(450, 560)):
                phi2   = math.acos(random.uniform(-0.25, 1.0))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(0.4, 2.0)
                vx = sp*math.sin(phi2)*math.cos(theta2)
                vy = sp*math.cos(phi2)
                vz = sp*math.sin(phi2)*math.sin(theta2)
                p(vx,vy,vz, random.randint(50,90), col=random.choice(GOLD_G),
                  drag=0.968, grav=2.2, size=1.9, hot=0.45)
            glitter_crown(n=120, sp_min=0.6, sp_max=2.4)

        # ── 분수 (Fountain) ───────────────────────────────────────────────────
        elif s == 'fountain':
            arches = _arms if _arms > 0 else random.randint(8, 12)
            for arm in range(arches):
                theta2 = (arm/arches)*2*math.pi
                for k2 in range(random.randint(22, 32)):
                    sp = 0.10 + k2*0.055
                    vx = sp*math.cos(theta2) + random.gauss(0, 0.04)
                    vy = 1.25 - k2*0.038 + random.gauss(0, 0.05)
                    vz = sp*math.sin(theta2) + random.gauss(0, 0.04)
                    p(vx,vy,vz, random.randint(72,115), col=pal[arm%len(pal)],
                      drag=0.973, grav=2.4, size=2.0)
            for _ in range(70):
                vx,vy,vz = upper_v(random.uniform(0.18, 0.75), 0.25)
                p(vx,vy,vz, random.randint(50,85), size=2.6, drag=0.977, grav=2.6)

        # ── 나이아가라 (Niagara) ──────────────────────────────────────────────
        elif s == 'waterfall_fw':
            # 넓은 수평 퍼짐 + 극강 낙하 → 나이아가라 폭포 커튼
            for _ in range(random.randint(520, 640)):
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(0.2, 1.3)
                vx = sp*math.cos(theta2)
                vy = random.uniform(-0.15, 0.35)
                vz = sp*math.sin(theta2)
                p(vx,vy,vz, random.randint(85,135), drag=0.960, grav=5.5, size=1.8)
            for _ in range(80):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.5))
                p(vx,vy,vz, random.randint(20,45), size=3.0, drag=0.978)

        # ── 나비 (Butterfly) ──────────────────────────────────────────────────
        elif s == 'butterfly':
            n = random.randint(620, 780)
            for i in range(n):
                t2  = (i/n)*4*math.pi
                r2  = (math.exp(math.sin(t2))
                       - 2*math.cos(4*t2)
                       + math.sin((2*t2-math.pi)/24)**5)
                sc  = random.gauss(0.27, 0.022)
                vx  = sc*r2*math.cos(t2) + random.gauss(0, 0.035)
                vz  = sc*r2*math.sin(t2) + random.gauss(0, 0.035)
                vy  = random.gauss(0, 0.045)
                c2  = pal[i % len(pal)]
                p(vx,vy,vz, random.randint(72,112), col=c2, drag=0.981, grav=0.45, size=1.9)
            for _ in range(50):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.18))
                p(vx,vy,vz, random.randint(25,50), size=3.0, drag=0.985)

        # ── 집속탄 (Cluster Bomb) ─────────────────────────────────────────────
        elif s == 'cluster_bomb':
            sub_cnt = random.randint(8, 12)
            for si in range(sub_cnt):
                svx,svy,svz = sphere_v(random.uniform(0.8, 1.8))
                sx = ox + svx*4.5; sy = oy + svy*3.5; sz2 = oz + svz*4.5
                col2 = pal[si % len(pal)]
                for _ in range(random.randint(52, 78)):
                    vx2,vy2,vz2 = sphere_v(random.uniform(0.3, 0.95))
                    parts.append(Particle(sx,sy,sz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          col2, random.randint(42,72),
                                          2.1, 0.976, _gmul))
                for _ in range(10):
                    vx2,vy2,vz2 = sphere_v(random.uniform(0.2, 0.7))
                    parts.append(Particle(sx,sy,sz2, vx2*_bsz, vy2*_bsz, vz2*_bsz,
                                          (1.0,1.0,0.8), random.randint(5,15),
                                          3.4, 0.963, _gmul, 0.90))

        # ── 혜성군 (Comet Shower) ─────────────────────────────────────────────
        elif s == 'comet_shower':
            comets = random.randint(6, 10)
            for ci in range(comets):
                main_t = (ci/comets)*2*math.pi
                cnt2 = random.randint(50, 72)
                for k2 in range(cnt2):
                    sigma2 = 0.06 + k2*0.003
                    t2 = main_t + random.gauss(0, sigma2)
                    sp = random.gauss(1.02, 0.14) * max(0.3, 1.0 - k2/cnt2)
                    sp = max(0.08, sp)
                    vx = sp*math.cos(t2); vz = sp*math.sin(t2)
                    vy = random.gauss(0.05, 0.07)
                    sz = 2.2 if k2 < cnt2//3 else 1.6
                    p(vx,vy,vz, random.randint(58,95), col=pal[ci%len(pal)],
                      drag=0.970, grav=1.25, size=sz)

        # ── 선화 (Senko) ──────────────────────────────────────────────────────
        elif s == 'senko':
            SENKO_C = [(1.0,0.92,0.30),(1.0,0.85,0.10),(1.0,1.0,0.60),(0.95,0.80,0.20)]
            arms3 = _arms if _arms > 0 else random.randint(14, 22)
            for arm in range(arms3):
                theta2 = (arm/arms3)*2*math.pi
                cnt = random.randint(20, 30)
                for k2 in range(cnt):
                    sp  = 0.05 + k2*0.052
                    jit = random.gauss(0, 0.03)
                    vx  = sp*math.cos(theta2+jit)
                    vy  = sp*random.gauss(0, 0.05)
                    vz  = sp*math.sin(theta2+jit)
                    p(vx,vy,vz, random.randint(85,135), col=random.choice(SENKO_C),
                      drag=0.977, grav=1.0, size=1.6, hot=0.30)
            for _ in range(55):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.25))
                p(vx,vy,vz, random.randint(35,65), col=(1.0,1.0,0.9), size=2.8, drag=0.984)

        # ── 폴링 리브스 (Falling Leaves) ─────────────────────────────────────
        elif s == 'falling_leaves':
            LEAF_COLS = [(1.0,0.30,0.10),(0.95,0.70,0.0),(0.25,0.85,0.25),
                         (0.85,0.30,0.95),(0.30,0.65,1.0),(1.0,0.55,0.15),
                         (1.0,0.95,0.30),(0.60,0.90,0.40)]
            n_leaves = random.randint(85, 120)
            for _ in range(n_leaves):
                phi2   = math.acos(random.uniform(0.0, 1.0))
                sp = random.uniform(0.4, 1.2) * _bsz
                vy_init = sp * math.cos(phi2)
                life = random.randint(160, 270)
                parts.append(LeafParticle(ox, oy, oz, vy_init,
                                          random.choice(LEAF_COLS), life))

        # ── 지뢰형 (Mine) ─────────────────────────────────────────────────────
        elif s == 'mine':
            # 지면 발사점에서 V형 부채꼴 30~45°로 금/주황 별들이 한꺼번에 솟구침
            MINE_GOLD = [(1.0,0.90,0.30),(1.0,0.75,0.12),(1.0,0.60,0.05),
                         (1.0,0.85,0.38),(0.95,0.68,0.0),(1.0,0.95,0.45)]
            n_balls = random.randint(35, 50)
            for bi in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))  # 수직 ±14° 이내
                theta2 = random.uniform(0, 2*math.pi)
                sp_ball = random.gauss(4.2, 0.65); sp_ball = max(1.8, sp_ball)
                bvx = sp_ball*math.sin(phi2)*math.cos(theta2)
                bvy = sp_ball*math.cos(phi2)
                bvz = sp_ball*math.sin(phi2)*math.sin(theta2)
                col2 = random.choice(MINE_GOLD)
                for _ in range(random.randint(3, 5)):
                    vx2 = bvx + random.gauss(0, 0.08)
                    vy2 = bvy + random.gauss(0, 0.08)
                    vz2 = bvz + random.gauss(0, 0.08)
                    p(vx2, vy2, vz2, random.randint(140, 195),
                      col=col2, drag=0.982, grav=0.2, size=10.0, hot=0.75)
            # 발화 순간 중심 화염 (고온 섬광)
            for _ in range(20):
                vx,vy,vz = sphere_v(random.uniform(0.2, 0.9))
                p(vx, vy, vz, random.randint(10, 28),
                  col=(1.0, random.uniform(0.65, 0.95), 0.15),
                  size=5.0, drag=0.990, grav=0.2, hot=0.96)

        # ── 팬 마인 (Mine Fan) ────────────────────────────────────────────────
        # 빠르게 치솟다 소멸 — 팔레트 색 트레이서
        elif s == 'mine_fan':
            n_balls = random.randint(55, 75)
            for _ in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(5.5, 8.5)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                col2 = random.choice(pal)
                # hot=0.35: 초반 순백 후 팔레트 색이 확실히 보임
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(40, 65),
                                      size=7.0, drag=0.984, grav=0.40,
                                      hot=0.35, spark=True))
            for _ in range(20):
                vx,vy,vz = sphere_v(random.uniform(0.3, 0.9))
                p(vx, vy, vz, random.randint(8, 20),
                  col=random.choice(pal), size=8.0, drag=0.987, grav=0.3, hot=0.40)

        # ── 컬러 마인 (Mine Color) ────────────────────────────────────────────
        # 방위각 구역별로 팔레트 색 분리, 꼬리 포함
        elif s == 'mine_color':
            n_sectors = len(pal)
            per_sec   = random.randint(14, 20)
            for si, col2 in enumerate(pal):
                sec_s = (si / n_sectors) * 2 * math.pi
                sec_e = ((si + 1) / n_sectors) * 2 * math.pi
                for _ in range(per_sec):
                    phi2   = math.acos(random.uniform(0.97, 1.00))
                    theta2 = random.uniform(sec_s, sec_e)
                    sp     = random.gauss(5.0, 0.6); sp = max(2.8, sp)
                    bvx = sp*math.sin(phi2)*math.cos(theta2)
                    bvy = sp*math.cos(phi2)
                    bvz = sp*math.sin(phi2)*math.sin(theta2)
                    parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                          col2, random.randint(90, 140),
                                          size=8.0, drag=0.983, grav=0.32,
                                          hot=0.38, spark=True))
            for _ in range(20):
                vx,vy,vz = sphere_v(random.uniform(0.2, 0.7))
                p(vx, vy, vz, random.randint(8, 20),
                  col=random.choice(pal), size=8.0, drag=0.989, grav=0.2, hot=0.42)

        # ── 나선 마인 (Mine Spiral) ───────────────────────────────────────────
        # 나선 배열, 팔레트 색 꼬리
        elif s == 'mine_spiral':
            n_turns    = random.randint(2, 3)
            n_per_turn = random.randint(16, 24)
            total      = n_turns * n_per_turn
            for i in range(total):
                t      = i / total
                theta2 = t * n_turns * 2 * math.pi
                phi2   = math.acos(random.uniform(0.97, 1.00))
                sp     = random.gauss(4.8, 0.5); sp = max(2.5, sp)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                col2 = pal[i % len(pal)]
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(80, 130),
                                      size=14.0, drag=0.984, grav=0.28,
                                      hot=0.40, spark=True))
            for _ in range(20):
                vx,vy,vz = sphere_v(random.uniform(0.2, 0.8))
                p(vx, vy, vz, random.randint(8, 20),
                  col=random.choice(pal), size=16.0, drag=0.987, grav=0.25, hot=0.45)

        # ── 크래클 마인 (Mine Crackle) ────────────────────────────────────────
        # 팔레트 색 + 은백 혼합 크래클, strobe 깜빡임
        elif s == 'mine_crackle':
            n_balls = random.randint(70, 95)
            for _ in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.gauss(5.5, 1.0); sp = max(2.8, sp)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                # 팔레트 색과 흰색 교대 → 팔레트 반영하면서 크래클 느낌 유지
                col2 = random.choice(pal) if random.random() < 0.6 else (1.0, 1.0, 1.0)
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(55, 95),
                                      size=12.0, drag=0.978, grav=0.55,
                                      hot=0.38, spark=True, strobe=True))
                for _ in range(random.randint(1, 2)):
                    parts.append(Particle(ox, oy, oz,
                                          bvx + random.gauss(0, 0.5),
                                          bvy + random.gauss(0, 0.4),
                                          bvz + random.gauss(0, 0.5),
                                          (1.0, 1.0, 1.0), random.randint(18, 38),
                                          size=6.0, drag=0.960, grav=1.0,
                                          hot=0.30, spark=True))
            for _ in range(22):
                vx,vy,vz = sphere_v(random.uniform(0.3, 1.0))
                p(vx, vy, vz, random.randint(6, 18),
                  col=random.choice(pal), size=14.0, drag=0.986, grav=0.3, hot=0.42)

        # ── 드래곤 마인 (Mine Dragon) ─────────────────────────────────────────
        # 팔레트 색 헤드 + 속도 단계별 꼬리
        elif s == 'mine_dragon':
            n_balls = random.randint(48, 68)
            for _ in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.gauss(6.0, 1.0); sp = max(3.2, sp)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                col2 = random.choice(pal)
                # head: 팔레트 색 코어, 빠른 발광
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(90, 150),
                                      size=16.0, drag=0.978, grav=0.9,
                                      hot=0.42, spark=True))
                # tail: 점점 느린 꼬리 입자
                for k in range(1, 6):
                    f = 1.0 - k * 0.16
                    p(bvx*f, bvy*f, bvz*f,
                      max(8, random.randint(70, 120) - k * 16),
                      col=col2, drag=0.975, grav=0.9,
                      size=max(4.0, 13.0 - k * 2.0), hot=max(0.20, 0.38 - k*0.04))
            for _ in range(22):
                vx,vy,vz = sphere_v(random.uniform(0.4, 1.2))
                p(vx, vy, vz, random.randint(8, 22),
                  col=random.choice(pal), size=14.0, drag=0.983, grav=0.5, hot=0.45)

        # ── 타이탄 마인 (Mine Titan) ──────────────────────────────────────────
        # 팔레트 색 대규모 분수 + spark 꼬리 + 미니 버스트
        elif s == 'mine_titan':
            n_balls = random.randint(80, 110)
            for _ in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.gauss(6.2, 1.2); sp = max(3.5, sp)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                col2 = random.choice(pal)
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(100, 160),
                                      size=16.0, drag=0.983, grav=0.24,
                                      hot=0.40, spark=True))
                for _ in range(random.randint(3, 5)):
                    p(bvx + random.gauss(0, 0.55),
                      bvy + random.gauss(0, 0.40),
                      bvz + random.gauss(0, 0.55),
                      random.randint(28, 60), col=col2,
                      drag=0.966, grav=0.65, size=8.0, hot=0.35)
            for _ in range(28):
                vx,vy,vz = sphere_v(random.uniform(0.3, 1.2))
                p(vx, vy, vz, random.randint(8, 22),
                  col=random.choice(pal), size=16.0, drag=0.988, grav=0.2, hot=0.45)

        # ── 비 마인 (Mine Rain) ───────────────────────────────────────────────
        # 빠르게 치솟다 강한 중력에 비처럼 낙하, 팔레트 색
        elif s == 'mine_rain':
            n_balls = random.randint(52, 72)
            for _ in range(n_balls):
                phi2   = math.acos(random.uniform(0.97, 1.00))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.uniform(6.0, 9.5)
                bvx = sp*math.sin(phi2)*math.cos(theta2)
                bvy = sp*math.cos(phi2)
                bvz = sp*math.sin(phi2)*math.sin(theta2)
                col2 = random.choice(pal)
                parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                      col2, random.randint(190, 270),
                                      size=14.0, drag=0.989, grav=3.5,
                                      hot=0.38, spark=True))
                for k in range(3):
                    f = 1.0 - k * 0.25
                    p(bvx*f, bvy*f, bvz*f,
                      max(8, random.randint(60, 100) - k * 22),
                      col=col2, drag=0.985, grav=3.5,
                      size=max(4.0, 9.0 - k * 2.2), hot=max(0.18, 0.32 - k*0.07))
            for _ in range(20):
                vx,vy,vz = sphere_v(random.uniform(0.3, 0.9))
                p(vx, vy, vz, random.randint(6, 18),
                  col=random.choice(pal), size=14.0, drag=0.988, grav=0.3, hot=0.42)

        # ── 꽃 마인 (Mine Flower) ─────────────────────────────────────────────
        # 꽃잎 배열, 팔레트 색 spark 꼬리 + 미니 버스트
        elif s == 'mine_flower':
            n_petals  = random.randint(5, 8)
            per_petal = random.randint(10, 16)
            for pi_idx in range(n_petals):
                petal_az = (pi_idx / n_petals) * 2 * math.pi
                col2 = pal[pi_idx % len(pal)]
                for j in range(per_petal):
                    narrow = 1.0 - abs(j / per_petal - 0.5) * 2
                    phi2   = math.acos(random.uniform(0.97, 1.00))
                    sp     = max(2.0, random.gauss(4.5, 0.5) * (0.65 + 0.35 * narrow))
                    theta2 = petal_az + random.gauss(0, 0.13)
                    bvx = sp*math.sin(phi2)*math.cos(theta2)
                    bvy = sp*math.cos(phi2)
                    bvz = sp*math.sin(phi2)*math.sin(theta2)
                    parts.append(Particle(ox, oy, oz, bvx, bvy, bvz,
                                          col2, random.randint(80, 130),
                                          size=14.0, drag=0.983, grav=0.30,
                                          hot=0.38, spark=True))
                    for _ in range(random.randint(2, 3)):
                        p(bvx + random.gauss(0, 0.45),
                          bvy + random.gauss(0, 0.35),
                          bvz + random.gauss(0, 0.45),
                          random.randint(20, 48), col=col2,
                          drag=0.962, grav=0.58, size=7.0, hot=0.30)
            for _ in range(16):
                vx,vy,vz = sphere_v(random.uniform(0.2, 0.7))
                p(vx, vy, vz, random.randint(6, 18),
                  col=random.choice(pal), size=14.0, drag=0.988, grav=0.2, hot=0.42)

        # ── 파스텔 (Pastel) ───────────────────────────────────────────────────
        elif s == 'pastel':
            PASTEL = [(1.0,0.72,0.72),(0.72,0.88,1.0),(0.82,1.0,0.75),(1.0,0.90,0.65),
                      (0.88,0.72,1.0),(0.72,1.0,0.96),(1.0,1.0,0.72)]
            for _ in range(random.randint(520, 640)):
                vx,vy,vz = sphere_v(random.gauss(0.85, 0.14))
                p(vx,vy,vz, random.randint(75,120), col=random.choice(PASTEL),
                  drag=0.983, grav=0.55, size=2.3, hot=0.12)
            for _ in range(55):
                vx,vy,vz = sphere_v(random.uniform(0.04, 0.20))
                p(vx,vy,vz, random.randint(28,55), col=(1.0,1.0,1.0), size=3.0, drag=0.986)

        # ── 유성 (Meteor) ─────────────────────────────────────────────────────
        elif s == 'meteor':
            METEOR = [(1.0,0.65,0.2),(1.0,0.45,0.0),(1.0,0.85,0.5),(0.9,0.7,0.3)]
            cnt_meteors = random.randint(8, 14)
            for mi in range(cnt_meteors):
                phi2   = math.acos(random.uniform(-0.95, -0.10))
                theta2 = random.uniform(0, 2*math.pi)
                sp     = random.gauss(1.08, 0.18); sp = max(0.4, sp)
                vxm = sp*math.sin(phi2)*math.cos(theta2)
                vym = sp*math.cos(phi2)
                vzm = sp*math.sin(phi2)*math.sin(theta2)
                for k2 in range(random.randint(22, 36)):
                    fade = max(0.2, 1.0 - k2/38)
                    vx2 = vxm*fade + random.gauss(0, 0.055)
                    vy2 = vym*fade + random.gauss(0, 0.038)
                    vz2 = vzm*fade + random.gauss(0, 0.055)
                    p(vx2,vy2,vz2, random.randint(42,82), col=random.choice(METEOR),
                      drag=0.966, grav=2.8, size=2.0-k2*0.022)
            for _ in range(100):
                vx,vy,vz = sphere_v(random.uniform(0.1, 0.7))
                p(vx,vy,vz, random.randint(22,48), col=random.choice(METEOR),
                  size=2.6, drag=0.974, grav=2.2)

        # ── 피쉬 (Fish) ───────────────────────────────────────────────────────
        elif s == 'fish':
            # 1단계: 폭발 섬광
            for _ in range(random.randint(30, 50)):
                vx,vy,vz = sphere_v(random.uniform(0.25, 0.75) * _bsz)
                parts.append(Particle(ox,oy,oz, vx,vy,vz,
                                      (1.0, random.uniform(0.80, 1.0), 0.5),
                                      random.randint(6, 18),
                                      size=3.0, drag=0.972, grav=0.7, hot=0.85))
            # 2단계: 물고기 파티클 10~15마리 생성
            n_fish = random.randint(10, 15)
            for _ in range(n_fish):
                vx,vy,vz = sphere_v(random.uniform(0.05, 0.14) * _bsz)
                life = int(random.uniform(0.6, 1.1) * FPS)
                col  = random.choice(pal)
                parts.append(FishParticle(ox, oy, oz, vx, vy, vz, col, life))

        # mine 계열 / comet / strobe / star / fish: 자체 효과로 완결 → 공통 섬광 전부 생략
        if s.startswith('mine') or s in ('comet', 'strobe', 'star', 'fish', 'falling_leaves'):
            return parts

        # ── 폭발 순간 섬광 (Break Flash) ─────────────────────────────────────
        for _ in range(random.randint(55, 75)):
            vx,vy,vz = sphere_v(random.uniform(1.0, 3.2) * _bsz)
            parts.append(Particle(ox,oy,oz, vx,vy,vz,
                                  (1.0,1.0,0.95), random.randint(4, 9),
                                  size=random.uniform(2.5,4.5),
                                  drag=0.958, grav=0.4, hot=1.0))
        # 폭발 연기 잔여 (느리게 퍼지는 회색)
        SMOKE = [(0.45,0.42,0.38),(0.38,0.35,0.30),(0.52,0.49,0.44)]
        for _ in range(random.randint(18, 26)):
            vx,vy,vz = sphere_v(random.uniform(0.05, 0.45))
            parts.append(Particle(ox,oy,oz, vx,vy,vz,
                                  random.choice(SMOKE), random.randint(55, 95),
                                  size=random.uniform(1.0, 2.2),
                                  drag=0.990, grav=0.08, hot=0.0))

        # ── 공통: 중심 대섬광 ────────────────────────────────────────────────
        for _ in range(random.randint(40, 60)):
            vx,vy,vz = sphere_v(random.uniform(0.8, 2.5) * _bsz)
            parts.append(Particle(ox,oy,oz, vx,vy,vz,
                                  (1.0,1.0,1.0), random.randint(12,28),
                                  3.5, 0.965, _gmul*1.2, hot=1.0))
        # 극초단 섬광 (순간 밝기)
        for _ in range(30):
            vx,vy,vz = sphere_v(random.uniform(0.3, 1.0))
            parts.append(Particle(ox,oy,oz, vx,vy,vz,
                                  (1.0,1.0,0.95), random.randint(5,12),
                                  4.5, 0.980, 0.8, hot=1.0))

        # ── 파티클 수 배율 적용 ────────────────────────────────────────────────
        pm = self.part_mul
        if pm < 1.0:
            keep = max(5, int(len(parts) * pm))
            parts = random.sample(parts, min(keep, len(parts)))
        elif pm > 1.05:
            n_extra = int(len(parts) * (pm - 1.0))
            for ep in random.choices(parts, k=n_extra):
                parts.append(Particle(
                    ep.x, ep.y, ep.z,
                    ep.vx+random.gauss(0,0.04), ep.vy+random.gauss(0,0.04), ep.vz+random.gauss(0,0.04),
                    (ep.r, ep.g, ep.b), ep.max_life, ep.size, ep.drag, ep.grav,
                    ep.hot, ep.spark))
        return parts

# ── 공유 코드 인코딩/디코딩 ──────────────────────────────────────────────────────
def fw_to_code(fw):
    """PlacedFirework → 공유 코드 문자열"""
    data = {
        'sh': fw.shape_idx, 'pl': fw.pal_idx, 'dl': round(fw.delay, 1),
        'bs': round(fw.burst_size, 2), 'pm': round(fw.part_mul, 2),
        'gm': round(fw.grav_mul, 2),  'dm': round(fw.drag_mul, 2),
        'lh': round(fw.launch_h, 1),
        'uc': int(fw.use_custom_col),
        'cc': [[round(v, 2) for v in c] for c in fw.custom_cols],
        'sp': round(fw.spread, 2),  'tl': round(fw.tail_len, 2),
        'wb': round(fw.wobble, 2),  'sc': round(fw.secondary, 2),
        'ac': fw.arm_count,         'lf': round(fw.lift, 2),
    }
    raw = json.dumps(data, separators=(',', ':'))
    return 'FW:' + base64.b64encode(raw.encode()).decode()

def code_to_fw_props(code):
    """공유 코드 → dict (None if invalid)"""
    try:
        if not code.startswith('FW:'):
            return None
        raw = base64.b64decode(code[3:].encode()).decode()
        d = json.loads(raw)
        return d
    except Exception:
        return None

# ── PlacedFirework ─────────────────────────────────────────────────────────────
class PlacedFirework:
    def __init__(self, x, z, shape_idx=0, pal_idx=0, delay=0.0,
                 burst_size=1.0, part_mul=1.0, grav_mul=1.0, drag_mul=1.0, launch_h=200.0,
                 use_custom_col=False, custom_cols=None,
                 spread=1.0, tail_len=1.0, wobble=0.0, secondary=1.0,
                 arm_count=0, lift=0.0,
                 launch_angle=0.0, launch_dir=0.0):
        self.x, self.z     = x, z
        self.shape_idx     = shape_idx
        self.pal_idx       = pal_idx
        self.delay         = delay
        self.fired         = False
        # 커스텀 속성
        self.burst_size    = burst_size
        self.part_mul      = part_mul
        self.grav_mul      = grav_mul
        self.drag_mul      = drag_mul
        self.launch_h      = launch_h
        self.use_custom_col = use_custom_col
        self.custom_cols   = custom_cols or [[1.0,0.2,0.0],[1.0,0.7,0.0],[1.0,1.0,0.3]]
        # 모양 세부
        self.spread        = spread
        self.tail_len      = tail_len
        self.wobble        = wobble
        self.secondary     = secondary
        self.arm_count     = arm_count
        self.lift          = lift
        # 발사 각도
        self.launch_angle  = launch_angle   # 수직에서 기울기 (0=직상, 최대 75°)
        self.launch_dir    = launch_dir     # 기울기 방향 (0=+X, 90=+Z, 도)

    def effective_palette(self):
        if self.use_custom_col:
            return [tuple(c) for c in self.custom_cols]
        return PALETTES[self.pal_idx]

    def make_rockets(self):
        shape_name = SHAPES[self.shape_idx]
        h = self.launch_h
        if shape_name.startswith('mine'):
            h = random.uniform(5, 12)

        # 코멧 부채꼴: arm_count >= 2이면 여러 발 동시 발사
        n = self.arm_count if (shape_name == 'comet' and self.arm_count >= 2) else 1

        rockets = []
        for i in range(n):
            target_y = random.uniform(h * 0.85, h * 1.15)
            if shape_name.startswith('mine'):
                target_y = GROUND_Y + random.uniform(1.0, 2.5)  # 지면에서 즉시 폭발
            r = Rocket(self.x, self.z, target_y, shape_name, self.effective_palette())
            r.burst_size = self.burst_size
            r.part_mul   = self.part_mul
            r.grav_mul   = self.grav_mul
            r.drag_mul   = self.drag_mul
            r.spread     = self.spread
            r.tail_len   = self.tail_len
            r.wobble     = self.wobble
            r.secondary  = self.secondary
            r.arm_count  = self.arm_count
            r.lift       = self.lift
            # 발사 각도 적용
            if self.launch_angle > 0.5 and n == 1:
                theta = math.radians(min(75.0, self.launch_angle))
                phi   = math.radians(self.launch_dir)
                base  = r.vy
                r.vx += math.sin(theta) * math.cos(phi) * base
                r.vz += math.sin(theta) * math.sin(phi) * base
                r.vy  = math.cos(theta) * base
            if n > 1:
                tilt = math.radians(22)
                azimuth = (i / n) * 2 * math.pi
                spd = random.uniform(1.8, 2.3)
                r.vx = spd * math.sin(tilt) * math.cos(azimuth)
                r.vz = spd * math.sin(tilt) * math.sin(azimuth)
                r.vy = spd * math.cos(tilt)
            rockets.append(r)
        return rockets

    def draw(self, selected=False):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        # 받침대 (회색 Roblox 파트)
        gl_box(self.x, GROUND_Y, self.z, 2.0, 0.6, 2.0, (0.63,0.63,0.63))
        # 발사통 (어두운 파이프)
        gl_cylinder(self.x, GROUND_Y+0.6, self.z, 0.38, 3.8, (0.25,0.25,0.25))
        gl_cylinder(self.x, GROUND_Y+0.6, self.z, 0.44, 3.8, (0.18,0.18,0.18), wire=True)
        # 선택: 파란 스타일 링
        if selected:
            glLineWidth(3.0)
            gl_ground_ring(self.x, self.z, 2.8, (0.0, 0.59, 0.91), 1.0)
            glLineWidth(1.5)
            gl_ground_ring(self.x, self.z, 3.2, (0.0, 0.59, 0.91), 0.5)
            glLineWidth(1.0)
        # 팔레트 색 링
        pc = self.effective_palette()[0]
        glLineWidth(2.0)
        gl_ground_ring(self.x, self.z, 2.0, pc, 0.9)
        glLineWidth(1.0)
        glDisable(GL_DEPTH_TEST)

# ── Structure ─────────────────────────────────────────────────────────────────
class Structure:
    def __init__(self, x, z, type_idx=0, scale=1.0):
        self.x, self.z = x, z
        self.type_idx = type_idx
        self.scale    = scale

    def draw(self, selected=False):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        s = self.scale
        x,z,y = self.x, self.z, GROUND_Y
        t = self.type_idx

        # 파트 색상 (회색 계열 + 와이어프레임 엣지)
        if t == 0:   # 빌딩
            col = (0.62, 0.63, 0.64)
            gl_box(x, y, z, 6*s, 18*s, 6*s, col)
            gl_box(x, y, z, 6*s, 18*s, 6*s, (0.45,0.46,0.48), 1.0, wire=True)
            for wy in range(3, int(16*s), 3):
                for wx in [-2,0,2]:
                    gl_box(x+wx*s, y+wy, z+3.05*s, 1.2*s, 1.5*s, 0.05, (0.72,0.90,1.0), 0.85)

        elif t == 1: # 기둥
            col = (0.60, 0.61, 0.62)
            gl_cylinder(x, y, z, 1.2*s, 14*s, col)
            gl_box(x, y,       z, 3*s, 0.8*s, 3*s, (0.55,0.56,0.57))
            gl_box(x, y+14*s,  z, 3*s, 0.8*s, 3*s, (0.55,0.56,0.57))

        elif t == 2: # 피라미드
            gl_pyramid(x, y, z, 12*s, 14*s, (0.64, 0.65, 0.66))

        elif t == 3: # 아치
            pw, ph, pt = 4*s, 14*s, 1.5*s
            col = (0.60, 0.61, 0.62)
            gl_box(x-pw, y, z, pt, ph, pt, col)
            gl_box(x+pw, y, z, pt, ph, pt, col)
            gl_box(x, y+ph-pt, z, pw*2+pt, pt, pt*1.2, col)

        elif t == 4: # 플랫폼
            gl_box(x, y,        z, 14*s, 1.2*s, 14*s, (0.55,0.56,0.57))
            gl_box(x, y+1.2*s,  z, 14*s, 0.5*s, 14*s, (0.66,0.67,0.68))

        if selected:
            glLineWidth(3.0)
            gl_ground_ring(x, z, 6*s+1, (0.0, 0.59, 0.91), 1.0)
            glLineWidth(1.5)
            gl_ground_ring(x, z, 6*s+2, (0.0, 0.59, 0.91), 0.4)
            glLineWidth(1.0)
        glDisable(GL_DEPTH_TEST)

# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.is_fullscreen = False
        self.sw = W
        self.sh = H
        self.screen = pygame.display.set_mode((W, H), DOUBLEBUF|OPENGL|RESIZABLE)
        pygame.display.set_caption("3D 폭죽 설치 게임")

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        # 거리 기반 포인트 크기 감쇠 (멀수록 작아짐)
        try:
            from OpenGL.GL import glPointParameterfv, GL_POINT_DISTANCE_ATTENUATION
            glPointParameterfv(GL_POINT_DISTANCE_ATTENUATION, [0.0, 0.0, 0.000012])
        except Exception:
            pass

        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(60, W/H, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)

        # 카메라
        # 카메라 (로블록스 스튜디오 스타일)
        self.yaw, self.pitch, self.dist = 30.0, 30.0, 90.0
        self.cam_target = [0.0, 0.0, 0.0]   # 궤도 중심
        self.rmb_down   = False              # 우클릭 상태
        self.mmb_down   = False              # 가운데 클릭 상태
        self.lmb_down   = False              # 좌클릭 상태
        self.lmb_start  = (0, 0)
        self.last_mouse = (0, 0)

        # GL 행렬 (picking용)
        self._mv = self._proj = self._vp = None
        self._eye_x = self._eye_z = 0.0

        # 씬
        self.placed_fw: list[PlacedFirework] = []
        self.placed_st: list[Structure]      = []
        self.rockets:   list[Rocket]         = []
        self.particles: list[Particle]       = []

        # 발사 시퀀스
        self.seq_active = False
        self.seq_start  = 0.0

        # UI 상태
        self.mode         = MODE_CAM
        self.selected     = None   # PlacedFirework or Structure
        self.cursor_pos   = None   # (x,y,z) on ground
        self.cur_shape    = 0
        self.cur_pal      = 0
        self.cur_st       = 0
        self.cur_scale    = 1.0
        self.cur_delay    = 0.0    # 배치할 폭죽의 기본 지연 (초)
        # 폭죽 커스텀 기본값
        self.cur_burst_size   = 1.0
        self.cur_part_mul     = 1.0
        self.cur_grav_mul     = 1.0
        self.cur_drag_mul     = 1.0
        self.cur_launch_h     = 200.0
        self.cur_use_cc       = False
        self.cur_custom_cols  = [[1.0,0.2,0.0],[1.0,0.7,0.0],[1.0,1.0,0.3]]
        # 모양 세부 기본값
        self.cur_spread       = 1.0
        self.cur_tail_len     = 1.0
        self.cur_wobble       = 0.0
        self.cur_secondary    = 1.0
        self.cur_arm_count    = 0
        self.cur_lift         = 0.0
        # 케이크 연발 폭죽
        self.cake_mode        = False   # True = 케이크 배치 모드
        self.cake_pattern     = 0       # 0=네모, 1=부채꼴
        self.cake_spd         = 0       # 속도 패턴 인덱스
        # 네모 패턴
        self.cake_rows        = 3
        self.cake_cols        = 4
        self.cake_spacing     = 5.0
        self.cake_dir_ang     = 0.0     # 격자 방향 (도)
        # 부채꼴 패턴
        self.cake_fan_n       = 7
        self.cake_fan_deg     = 120.0   # 부채꼴 펼침 각도
        self.cake_fan_dir     = 0.0     # 부채꼴 정면 방향
        self.cake_fan_tilt    = 25.0    # 발사 기울기 (도)
        # 폭죽 종류 시퀀스
        self.cake_shape_a     = 0       # 1번 종류
        self.cake_shape_b     = 6       # 2번 종류
        self.cake_seq         = 0       # 0=A만, 1=ABAB, 2=AABB, 3=랜덤
        # 단발 발사 각도
        self.cur_launch_angle = 0.0
        self.cur_launch_dir   = 0.0
        # FW 커스텀 패널
        self.fw_panel_open    = False
        self.fw_panel_tab     = 0   # 0=모양 1=속성 2=색상 3=공유
        self._fw_slider_drag  = None
        self._fw_slider_rects = []
        self._fw_btn_rects    = []
        self._fw_btn_topbar   = None
        self._world_drag      = None   # (object, ox, oz) — SELECT 모드 드래그 이동
        self._fw_import_active = False
        self._fw_import_buf    = ''
        self.cur_bg       = 0      # 현재 배경 인덱스
        self._stars       = []     # [(x,y,z), ...] 별 위치 캐시

        # 환경 설정
        b0 = BACKGROUNDS[0]
        self.env = {
            'sky_top':      list(b0['sky_top']),
            'sky_bot':      list(b0['sky_bot']),
            'ground':       list(b0['ground']),
            'grid':         list(b0['grid']),
            'grid2':        list(b0['grid2']),
            'stars':        b0['stars'],
            'cloud_count':  0,
            'cloud_speed':  0.3,
            'cloud_height': 15.0,
            'cloud_size':   1.0,
            # 그래픽 설정
            'fog_density':   0.0,
            'particle_size': 6.0,
            'show_grid':     1,    # 1=on 0=off
            'tile_detail':   1,    # 1=현실적 타일 0=단색
        }
        self.env_panel_open  = False
        self.env_tab         = 0   # 0=배경 1=하늘 2=지면 3=구름 4=그래픽
        self._env_slider_drag  = None  # (key, comp, rx, rw, vmin, vmax, is_int)
        self._env_slider_rects = []
        self._env_btn_rects    = []
        self._env_btn_topbar   = None
        self._clouds       = []    # [[wx, wz, size, phase], ...]
        self._cloud_time   = 0.0

        # DAW 타임라인 상태
        self.tl_zoom      = 80.0
        self.tl_offset    = 0.0
        self.tl_drag_fw   = None
        self.tl_drag_origin = 0.0
        self.tl_drag_mx   = 0
        # UI 인터랙션 영역 (draw 시 채워짐, click 시 사용)
        self._topbar_rects = []     # [(rect, mode), ...]
        self._play_rect    = None
        self._reset_rect   = None
        self._picker_rects = []     # [(rect, action, value), ...]

        _kor_fonts = ['malgun gothic', 'malgungothic', 'gulim', 'dotum', 'batang', 'nanum gothic', 'nanumgothic']
        _ui_font = next((f for f in _kor_fonts if pygame.font.match_font(f)), None) or 'segoe ui'
        self.font_lg = pygame.font.SysFont(_ui_font, 20, bold=True)
        self.font_sm = pygame.font.SysFont(_ui_font, 15)
        self.font_xs = pygame.font.SysFont(_ui_font, 13)
        self.clock   = pygame.time.Clock()
        self.running = True

    # ── 카메라 ────────────────────────────────────────────────────────────────
    def set_camera(self):
        glLoadIdentity()
        yr = math.radians(self.yaw); pr = math.radians(self.pitch)
        tx,ty,tz = self.cam_target
        cx = tx + self.dist*math.cos(pr)*math.sin(yr)
        cy = ty + self.dist*math.sin(pr)
        cz = tz + self.dist*math.cos(pr)*math.cos(yr)
        gluLookAt(cx,cy,cz, tx,ty,tz, 0,1,0)
        self._eye_x, self._eye_z = cx, cz
        self._mv   = glGetDoublev(GL_MODELVIEW_MATRIX)
        self._proj = glGetDoublev(GL_PROJECTION_MATRIX)
        self._vp   = glGetIntegerv(GL_VIEWPORT)

    # ── 지면 ray-cast ─────────────────────────────────────────────────────────
    def screen_to_ground(self, mx, my):
        if self._mv is None: return None
        wy = self._vp[3] - my
        try:
            near = gluUnProject(mx,wy,0.0, self._mv,self._proj,self._vp)
            far  = gluUnProject(mx,wy,1.0, self._mv,self._proj,self._vp)
        except: return None
        dy = far[1]-near[1]
        if abs(dy) < 1e-6: return None
        t = (GROUND_Y - near[1]) / dy
        if t < 0 or t > 2000: return None
        x = near[0]+t*(far[0]-near[0])
        z = near[2]+t*(far[2]-near[2])
        if abs(x)>10000 or abs(z)>10000: return None
        return (x, GROUND_Y, z)

    # ── 가장 가까운 배치 아이템 선택 ──────────────────────────────────────────
    def pick(self, mx, my):
        best, best_d = None, 30.0
        for fw in self.placed_fw:
            sx,sy = self._project(fw.x, GROUND_Y+2, fw.z)
            if sx is None: continue
            d = math.hypot(sx-mx, sy-my)
            if d < best_d: best,best_d = fw,d
        for st in self.placed_st:
            sx,sy = self._project(st.x, GROUND_Y+5, st.z)
            if sx is None: continue
            d = math.hypot(sx-mx, sy-my)
            if d < best_d: best,best_d = st,d
        return best

    def _project(self, x,y,z):
        if self._mv is None: return None,None
        try:
            wx,wy,_ = gluProject(x,y,z, self._mv,self._proj,self._vp)
            return wx * W // self.sw, (self.sh - wy) * H // self.sh
        except: return None,None

    # ── 이벤트 ────────────────────────────────────────────────────────────────
    def handle_events(self):
        self._pmx, self._pmy = pygame.mouse.get_pos()
        mx = self._pmx * W // self.sw
        my = self._pmy * H // self.sh
        for ev in pygame.event.get():
            if ev.type == QUIT: self.running = False
            elif ev.type == getattr(pygame, 'WINDOWRESIZED', -1):
                self._on_resize(ev.x, ev.y)

            elif ev.type == pygame.TEXTINPUT:
                if self._fw_import_active:
                    self._fw_import_buf += ev.text

            elif ev.type == KEYDOWN:
                k = ev.key
                # 텍스트 입력 중일 때
                if self._fw_import_active:
                    if k == K_RETURN or k == K_KP_ENTER:
                        self._fw_import_apply()
                    elif k == K_ESCAPE:
                        self._fw_import_active = False; self._fw_import_buf = ''
                    elif k == K_BACKSPACE:
                        self._fw_import_buf = self._fw_import_buf[:-1]
                    continue  # 다른 단축키 무시
                if k == K_ESCAPE: self.running = False
                # 모드 전환 (우클릭 안 눌린 상태에서만)
                elif not self.rmb_down:
                    if   k == K_1: self.mode = MODE_CAM
                    elif k == K_2: self.mode = MODE_FW
                    elif k == K_3: self.mode = MODE_ST
                    elif k == K_4: self.mode = MODE_SEL
                    elif k == K_F5: self._reset()
                    elif k == K_F11: self._toggle_fullscreen()
                    elif k == K_RETURN or k == K_KP_ENTER:
                        self._toggle_sequence()
                    elif k == K_f:
                        # F → 카메라 타겟 리셋 (Roblox Studio의 F-focus)
                        self.cam_target = [0.0, 0.0, 0.0]; self.dist = 90.0
                    elif k == K_t:
                        if self.mode == MODE_FW and self.selected is None:
                            self.cur_shape = (self.cur_shape+1) % len(SHAPES)
                        elif isinstance(self.selected, PlacedFirework):
                            self.selected.shape_idx = (self.selected.shape_idx+1)%len(SHAPES)
                    elif k == K_p:
                        if isinstance(self.selected, PlacedFirework):
                            self.selected.pal_idx = (self.selected.pal_idx+1)%len(PALETTES)
                        else:
                            self.cur_pal = (self.cur_pal+1) % len(PALETTES)
                    elif k == K_LEFTBRACKET:
                        if isinstance(self.selected, Structure):
                            self.selected.scale = max(0.3, self.selected.scale-0.2)
                        else: self.cur_scale = max(0.3, self.cur_scale-0.2)
                    elif k == K_RIGHTBRACKET:
                        if isinstance(self.selected, Structure):
                            self.selected.scale = min(4.0, self.selected.scale+0.2)
                        else: self.cur_scale = min(4.0, self.cur_scale+0.2)
                    elif k == K_LEFT:
                        if isinstance(self.selected, PlacedFirework):
                            self.selected.delay = max(0.0, round(self.selected.delay-0.5,1))
                        else: self.cur_delay = max(0.0, round(self.cur_delay-0.5,1))
                    elif k == K_RIGHT:
                        if isinstance(self.selected, PlacedFirework):
                            self.selected.delay = round(self.selected.delay+0.5,1)
                        else: self.cur_delay = round(self.cur_delay+0.5,1)
                    elif k == K_UP:
                        if self.mode == MODE_ST:
                            self.cur_st = (self.cur_st+1)%len(ST_TYPES)
                    elif k == K_DOWN:
                        if self.mode == MODE_ST:
                            self.cur_st = (self.cur_st-1)%len(ST_TYPES)
                    elif k == K_DELETE:
                        if self.selected in self.placed_fw: self.placed_fw.remove(self.selected)
                        elif self.selected in self.placed_st: self.placed_st.remove(self.selected)
                        self.selected = None
                    elif k == K_b:
                        self.cur_bg = (self.cur_bg + 1) % len(BACKGROUNDS)
                        self._apply_bg_preset(self.cur_bg)

            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 1:
                    self.lmb_down  = True
                    self.lmb_start = ev.pos
                    self.last_mouse = ev.pos
                    # 상단 바 버튼
                    if my < 42 and self._fw_btn_topbar and self._fw_btn_topbar.collidepoint(mx, my):
                        self.fw_panel_open = not self.fw_panel_open
                    elif my < 42 and self._env_btn_topbar and self._env_btn_topbar.collidepoint(mx, my):
                        self.env_panel_open = not self.env_panel_open
                    # FW 커스텀 패널 클릭
                    elif self.fw_panel_open and mx < FW_PANEL_W and 42 <= my < H - TL_H:
                        self._fw_panel_click(mx, my)
                    # 환경 패널 클릭
                    elif self.env_panel_open and mx >= W - ENV_PANEL_W and 42 <= my < H - TL_H:
                        self._env_panel_click(mx, my)
                    elif self._in_tl_track(mx, my):
                        hit = self._tl_hit_clip(mx)
                        if hit:
                            self.tl_drag_fw     = hit
                            self.tl_drag_origin = hit.delay
                            self.tl_drag_mx     = mx
                            self.selected       = hit
                    elif self._in_tl(my):
                        self._picker_rect_click(mx, my)
                    # SELECT 모드 — 오브젝트 드래그
                    elif self.mode == MODE_SEL and not self._in_tl(my):
                        hit = self.pick(mx, my)
                        if hit:
                            self.selected    = hit
                            self._world_drag = hit
                    # 상단 바 모드 탭
                    elif my < 42:
                        self._topbar_rect_click(mx, my)
                elif ev.button == 3:
                    self.rmb_down   = True
                    self.last_mouse = ev.pos
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                elif ev.button == 2:
                    self.mmb_down   = True
                    self.last_mouse = ev.pos
                elif ev.button == 4:
                    if self._in_tl(my):
                        self.tl_zoom = min(300, self.tl_zoom * 1.15)
                    else:
                        self._dolly(-1)
                elif ev.button == 5:
                    if self._in_tl(my):
                        self.tl_zoom = max(20, self.tl_zoom / 1.15)
                    else:
                        self._dolly(1)

            elif ev.type == MOUSEBUTTONUP:
                if ev.button == 1:
                    if self._fw_slider_drag:
                        self._fw_slider_drag = None
                    elif self._env_slider_drag:
                        self._env_slider_drag = None
                    elif self.tl_drag_fw:
                        self.tl_drag_fw = None
                    elif self._world_drag:
                        self._world_drag = None
                    elif math.hypot(ev.pos[0]-self.lmb_start[0],
                                    ev.pos[1]-self.lmb_start[1]) < 6:
                        on_panel = (
                            (self.fw_panel_open and mx < FW_PANEL_W and my >= 42) or
                            (self.env_panel_open and mx >= W - ENV_PANEL_W and my >= 42))
                        if not self._in_tl(my) and not on_panel:
                            self._on_click(mx, my)
                    self.lmb_down = False
                elif ev.button == 3:
                    self.rmb_down = False
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                elif ev.button == 2:
                    self.mmb_down = False

            elif ev.type == MOUSEMOTION:
                dx = ev.pos[0]-self.last_mouse[0]
                dy = ev.pos[1]-self.last_mouse[1]
                if self._fw_slider_drag:
                    self._fw_slider_update(mx)
                elif self._env_slider_drag:
                    self._env_update_slider(mx)
                elif self._world_drag is not None and self.lmb_down:
                    pos = self.screen_to_ground(self._pmx, self._pmy)
                    if pos is not None:
                        obj = self._world_drag
                        obj.x, obj.z = pos[0], pos[2]
                elif self.tl_drag_fw:
                    delta_s = (mx - self.tl_drag_mx) / self.tl_zoom
                    self.tl_drag_fw.delay = max(0.0, round((self.tl_drag_origin + delta_s)*10)/10)
                elif self.rmb_down:
                    self.yaw   += dx * 0.35
                    self.pitch  = max(-80, min(80, self.pitch - dy*0.35))
                elif self.mmb_down:
                    if self._in_tl(my):
                        self.tl_offset = max(0.0, self.tl_offset - dx * W / (self.sw * self.tl_zoom))
                    else:
                        self._pan(dx, dy)
                self.last_mouse = ev.pos

        # 커서 위치 업데이트
        self.cursor_pos = self.screen_to_ground(self._pmx, self._pmy)

    def _dolly(self, direction):
        """스크롤 줌: 시선 방향으로 카메라 접근/후퇴"""
        factor = 1.12 if direction > 0 else 0.89
        self.dist = max(5, min(300, self.dist * factor))

    def _pan(self, dx, dy):
        """가운데 드래그 패닝: 카메라 right/up 방향으로 타겟 이동"""
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)
        speed = self.dist * 0.0012
        # 카메라 right 벡터 (수평)
        rx = math.cos(yr); rz = -math.sin(yr)
        # 카메라 up 벡터 (pitch 고려)
        ux = -math.sin(pr)*math.sin(yr)
        uy =  math.cos(pr)
        uz = -math.sin(pr)*math.cos(yr)
        self.cam_target[0] -= (dx*rx - dy*ux) * speed
        self.cam_target[1] -= (         dy*uy) * speed
        self.cam_target[2] -= (dx*rz - dy*uz) * speed

    # ── 타임라인 헬퍼 ─────────────────────────────────────────────────────────
    def _in_tl(self, y):        return y >= H - TL_H
    def _in_tl_transport(self, y): return H - TL_H <= y < H - TL_H + TL_TRANSPORT
    def _in_tl_track(self, x, y):
        return x >= TL_PICK_W and y >= H - TL_H + TL_TRANSPORT + TL_RULER_H

    def _tl_x(self, delay):
        return TL_PICK_W + int((delay - self.tl_offset) * self.tl_zoom)

    def _tl_hit_clip(self, mx):
        for fw in self.placed_fw:
            if abs(mx - self._tl_x(fw.delay)) < CLIP_W//2 + 4:
                return fw
        return None

    def _picker_rect_click(self, mx, my):
        """_picker_rects에 등록된 버튼 검사"""
        for rect, action, val in self._picker_rects:
            if rect.collidepoint(mx, my):
                self._picker_action(action, val)
                return
        # transport 버튼
        if self._play_rect and self._play_rect.collidepoint(mx, my):
            self._toggle_sequence()
        if self._reset_rect and self._reset_rect.collidepoint(mx, my):
            self.seq_active = False
            for fw in self.placed_fw: fw.fired = False
            self.rockets.clear(); self.particles.clear()

    def _picker_action(self, action, val):
        """picker 버튼 액션 처리"""
        if action == 'shape':
            if self.mode == MODE_FW:
                self.cur_shape = val
            elif isinstance(self.selected, PlacedFirework):
                self.selected.shape_idx = val
        elif action == 'pal':
            if isinstance(self.selected, PlacedFirework):
                self.selected.pal_idx = val
            else:
                self.cur_pal = val
        elif action == 'cake_toggle':
            self.cake_mode = bool(val) if val is not None else not self.cake_mode
        elif action == 'cake_pattern':
            self.cake_pattern = val
        elif action == 'cake_spd':
            self.cake_spd = val
        elif action == 'cake_seq':
            self.cake_seq = val
        # 네모 패턴 조절
        elif action == 'cake_rows_dec':  self.cake_rows = max(1, self.cake_rows-1)
        elif action == 'cake_rows_inc':  self.cake_rows = min(10, self.cake_rows+1)
        elif action == 'cake_cols_dec':  self.cake_cols = max(1, self.cake_cols-1)
        elif action == 'cake_cols_inc':  self.cake_cols = min(10, self.cake_cols+1)
        elif action == 'cake_sp_dec':    self.cake_spacing = max(2.0, self.cake_spacing-1.0)
        elif action == 'cake_sp_inc':    self.cake_spacing = min(30.0, self.cake_spacing+1.0)
        elif action == 'cake_da_dec':    self.cake_dir_ang = (self.cake_dir_ang-15)%360
        elif action == 'cake_da_inc':    self.cake_dir_ang = (self.cake_dir_ang+15)%360
        # 부채꼴 패턴 조절
        elif action == 'cake_fn_dec':    self.cake_fan_n = max(2, self.cake_fan_n-1)
        elif action == 'cake_fn_inc':    self.cake_fan_n = min(24, self.cake_fan_n+1)
        elif action == 'cake_fd_dec':    self.cake_fan_deg = max(10.0, self.cake_fan_deg-10)
        elif action == 'cake_fd_inc':    self.cake_fan_deg = min(360.0, self.cake_fan_deg+10)
        elif action == 'cake_fdir_dec':  self.cake_fan_dir = (self.cake_fan_dir-15)%360
        elif action == 'cake_fdir_inc':  self.cake_fan_dir = (self.cake_fan_dir+15)%360
        elif action == 'cake_ft_dec':    self.cake_fan_tilt = max(0.0, self.cake_fan_tilt-5)
        elif action == 'cake_ft_inc':    self.cake_fan_tilt = min(75.0, self.cake_fan_tilt+5)
        # 폭죽 종류 A/B
        elif action == 'cake_sa_dec':    self.cake_shape_a = (self.cake_shape_a-1)%len(SHAPES)
        elif action == 'cake_sa_inc':    self.cake_shape_a = (self.cake_shape_a+1)%len(SHAPES)
        elif action == 'cake_sb_dec':    self.cake_shape_b = (self.cake_shape_b-1)%len(SHAPES)
        elif action == 'cake_sb_inc':    self.cake_shape_b = (self.cake_shape_b+1)%len(SHAPES)
        # 단발 발사 각도
        elif action == 'lang_dec':   self.cur_launch_angle = max(0.0, self.cur_launch_angle-5)
        elif action == 'lang_inc':   self.cur_launch_angle = min(75.0, self.cur_launch_angle+5)
        elif action == 'ldir_dec':   self.cur_launch_dir = (self.cur_launch_dir-15)%360
        elif action == 'ldir_inc':   self.cur_launch_dir = (self.cur_launch_dir+15)%360
        elif action == 'delay_dec':
            if isinstance(self.selected, PlacedFirework):
                self.selected.delay = max(0.0, round(self.selected.delay - 0.5, 1))
            else:
                self.cur_delay = max(0.0, round(self.cur_delay - 0.5, 1))
        elif action == 'delay_inc':
            if isinstance(self.selected, PlacedFirework):
                self.selected.delay = round(self.selected.delay + 0.5, 1)
            else:
                self.cur_delay = round(self.cur_delay + 0.5, 1)
        elif action == 'scale_dec':
            if isinstance(self.selected, Structure):
                self.selected.scale = max(0.3, round(self.selected.scale - 0.2, 1))
            else:
                self.cur_scale = max(0.3, round(self.cur_scale - 0.2, 1))
        elif action == 'scale_inc':
            if isinstance(self.selected, Structure):
                self.selected.scale = min(4.0, round(self.selected.scale + 0.2, 1))
            else:
                self.cur_scale = min(4.0, round(self.cur_scale + 0.2, 1))
        elif action == 'st_type':
            if self.mode == MODE_ST:
                self.cur_st = val
            elif isinstance(self.selected, Structure):
                self.selected.type_idx = val
        elif action == 'delete':
            if self.selected in self.placed_fw:
                self.placed_fw.remove(self.selected)
            elif self.selected in self.placed_st:
                self.placed_st.remove(self.selected)
            self.selected = None
        elif action == 'mode':
            self.mode = val

    def _topbar_rect_click(self, mx, my):
        for rect, mode in self._topbar_rects:
            if rect.collidepoint(mx, my):
                self.mode = mode
                return

    def _on_click(self, mx, my):
        if self.mode == MODE_CAM: return
        pos = self.screen_to_ground(self._pmx, self._pmy)
        if pos is None: return
        x,_,z = pos

        if self.mode == MODE_FW:
            hit = self.pick(mx, my)
            if isinstance(hit, PlacedFirework):
                self.selected = hit
            elif self.cake_mode:
                # ── 케이크 연발 배치 ──────────────────────────────────────
                self.selected = None
                if self.cake_pattern == 0:  # 네모
                    shots = _cake_build_rect(x, z, self.cake_rows, self.cake_cols,
                                             self.cake_spacing, self.cake_dir_ang)
                else:                        # 부채꼴
                    shots = _cake_build_fan(x, z, self.cake_fan_n, self.cake_fan_deg,
                                            self.cake_fan_dir, self.cake_fan_deg,
                                            self.cake_fan_tilt)
                delays = _cake_delays(len(shots), self.cake_spd)
                for idx, ((fx, fz, lang, ldir), dt) in enumerate(zip(shots, delays)):
                    fw = PlacedFirework(fx, fz, self.cur_shape, self.cur_pal,
                                       round(self.cur_delay + dt, 2),
                                       self.cur_burst_size, self.cur_part_mul,
                                       self.cur_grav_mul,   self.cur_drag_mul,
                                       self.cur_launch_h,   self.cur_use_cc,
                                       [list(c) for c in self.cur_custom_cols],
                                       self.cur_spread, self.cur_tail_len,
                                       self.cur_wobble, self.cur_secondary,
                                       self.cur_arm_count, self.cur_lift,
                                       lang, ldir)
                    self.placed_fw.append(fw)
            else:
                # 단발 배치
                self.selected = None
                fw = PlacedFirework(x, z, self.cur_shape, self.cur_pal, self.cur_delay,
                                    self.cur_burst_size, self.cur_part_mul,
                                    self.cur_grav_mul,   self.cur_drag_mul,
                                    self.cur_launch_h,   self.cur_use_cc,
                                    [list(c) for c in self.cur_custom_cols],
                                    self.cur_spread, self.cur_tail_len,
                                    self.cur_wobble, self.cur_secondary,
                                    self.cur_arm_count, self.cur_lift,
                                    self.cur_launch_angle, self.cur_launch_dir)
                self.placed_fw.append(fw)

        elif self.mode == MODE_ST:
            st = Structure(x, z, self.cur_st, self.cur_scale)
            self.placed_st.append(st)

        elif self.mode == MODE_SEL:
            self.selected = self.pick(mx, my)

    def _on_resize(self, w, h):
        self.sw, self.sh = w, h
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, w / h, 0.5, 2000)
        glMatrixMode(GL_MODELVIEW)

    def _toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), DOUBLEBUF|OPENGL|FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((W, H), DOUBLEBUF|OPENGL|RESIZABLE)
        info = pygame.display.Info()
        self._on_resize(info.current_w, info.current_h)

    def _toggle_sequence(self):
        if self.seq_active:
            self.seq_active = False
            for fw in self.placed_fw: fw.fired = False
        else:
            if not self.placed_fw: return
            for fw in self.placed_fw: fw.fired = False
            self.rockets.clear(); self.particles.clear()
            self.seq_active = True
            self.seq_start  = time.time()

    def _apply_bg_preset(self, idx):
        b = BACKGROUNDS[idx]
        self.env['sky_top'] = list(b['sky_top'])
        self.env['sky_bot'] = list(b['sky_bot'])
        self.env['ground']  = list(b['ground'])
        self.env['grid']    = list(b['grid'])
        self.env['grid2']   = list(b['grid2'])
        self.env['stars']   = b['stars']
        self._stars = []

    def _reset(self):
        self.placed_fw.clear(); self.placed_st.clear()
        self.rockets.clear(); self.particles.clear()
        self.seq_active = False; self.selected = None

    # ── 업데이트 ──────────────────────────────────────────────────────────────
    def update(self):
        # WASD 카메라 이동 (항상 동작)
        if True:
            keys  = pygame.key.get_pressed()
            shift = keys[K_LSHIFT] or keys[K_RSHIFT]
            spd   = (self.dist * 0.008) * (0.25 if shift else 1.0)
            yr = math.radians(self.yaw)
            # 수평 forward/right 벡터
            fx = -math.sin(yr); fz = -math.cos(yr)
            rx =  math.cos(yr); rz = -math.sin(yr)
            if keys[K_w]:
                self.cam_target[0] += fx*spd; self.cam_target[2] += fz*spd
            if keys[K_s]:
                self.cam_target[0] -= fx*spd; self.cam_target[2] -= fz*spd
            if keys[K_a]:
                self.cam_target[0] -= rx*spd; self.cam_target[2] -= rz*spd
            if keys[K_d]:
                self.cam_target[0] += rx*spd; self.cam_target[2] += rz*spd
            if keys[K_e]: self.cam_target[1] += spd
            if keys[K_q]: self.cam_target[1] -= spd

        # 시퀀스 발사
        if self.seq_active:
            elapsed = time.time()-self.seq_start
            for fw in self.placed_fw:
                if not fw.fired and elapsed >= fw.delay:
                    self.rockets.extend(fw.make_rockets())
                    fw.fired = True
            if all(fw.fired for fw in self.placed_fw):
                if not self.rockets and not self.particles:
                    self.seq_active = False
                    for fw in self.placed_fw: fw.fired = False

        # 로켓
        alive = []
        for r in self.rockets:
            if r.update(): alive.append(r)
            elif len(self.particles) < MAX_PART:
                self.particles.extend(r.explode())
        self.rockets = alive

        # 로켓 trail 방출 — 형태별 차별화
        if len(self.particles) < MAX_PART:
            for r in self.rockets:
                if r.shape == 'comet':
                    # 혜성 굵고 선명한 꼬리 — 발사부터 소멸까지
                    for _ in range(random.randint(38, 55)):
                        svx = r.vx*random.uniform(-0.32, 0.06) + random.gauss(0, 0.04)
                        svy = r.vy*random.uniform(-0.90, -0.12) + random.gauss(0, 0.06)
                        svz = r.vz*random.uniform(-0.32, 0.06) + random.gauss(0, 0.04)
                        life = random.randint(38, 75)
                        col  = random.choice(r.palette)
                        self.particles.append(
                            Particle(r.x, r.y, r.z, svx, svy, svz,
                                     col, life, size=3.8, drag=0.970, grav=0.7, hot=0.62))
                    # 고온 핵 (대형)
                    self.particles.append(
                        Particle(r.x, r.y, r.z, 0, 0, 0,
                                 (1.0,1.0,0.97), 4, size=8.5, drag=0.99, grav=0.01, hot=1.0))
                    # 보조 코어
                    self.particles.append(
                        Particle(r.x, r.y, r.z, 0, 0, 0,
                                 (1.0,0.92,0.70), 6, size=5.0, drag=0.98, grav=0.03, hot=0.92))

                elif r.shape == 'mine':
                    # 마인 — 짧은 상승 중 불꽃 연기
                    for _ in range(random.randint(6, 10)):
                        svx = r.vx + random.gauss(0, 0.14)
                        svy = r.vy * random.uniform(-0.5, -0.04) + random.gauss(0, 0.09)
                        svz = r.vz + random.gauss(0, 0.14)
                        self.particles.append(
                            Particle(r.x, r.y, r.z, svx, svy, svz,
                                     (1.0, random.uniform(0.5, 0.8), 0.2),
                                     random.randint(5, 14), size=2.4, drag=0.972, grav=1.9, hot=0.75))

                elif r.shape == 'strobe':
                    # 스트로브 별 — 로켓 위치에 깜빡이는 밝은 점
                    for _ in range(random.randint(4, 7)):
                        svx = random.gauss(0, 0.04)
                        svy = random.gauss(0, 0.04)
                        svz = random.gauss(0, 0.04)
                        life = random.randint(18, 35)
                        self.particles.append(
                            Particle(r.x, r.y, r.z, svx, svy, svz,
                                     (1.0,1.0,1.0), life,
                                     size=3.8, drag=0.992, grav=0.15,
                                     hot=0.0, strobe=True))

                else:
                    # 기본 크래클 스파크
                    for _ in range(random.randint(2, 4)):
                        svx = r.vx*random.uniform(-0.4,0.2) + random.gauss(0, 0.18)
                        svy = r.vy*random.uniform(-0.5,0.0) + random.gauss(0, 0.12)
                        svz = r.vz*random.uniform(-0.4,0.2) + random.gauss(0, 0.18)
                        life = random.randint(8, 18)
                        self.particles.append(
                            Particle(r.x, r.y, r.z, svx, svy, svz,
                                     (1.0, random.uniform(0.55,0.85), 0.15),
                                     life, size=1.2, drag=0.945, grav=2.8,
                                     hot=0.9, spark=True))

        # 물고기 잔상 꼬리 — 각 FishParticle 뒤에 짧고 밝은 trail 생성
        if len(self.particles) < MAX_PART:
            fish_trails = []
            for p in self.particles:
                if isinstance(p, FishParticle):
                    fish_trails.append(
                        Particle(p.x, p.y, p.z,
                                 p.vx * random.uniform(0.0, 0.12) + random.gauss(0, 0.012),
                                 p.vy * random.uniform(0.0, 0.12) + random.gauss(0, 0.012),
                                 p.vz * random.uniform(0.0, 0.12) + random.gauss(0, 0.012),
                                 (p.r, p.g, p.b), random.randint(3, 9),
                                 size=p.size * 0.52, drag=0.989, grav=0.35, hot=0.92))
            self.particles.extend(fish_trails)

        # 파티클
        self.particles = [p for p in self.particles if p.update()]

        # 구름 애니메이션
        dt = 1.0 / FPS
        self._cloud_time += dt
        n = self.env['cloud_count']
        if len(self._clouds) != n:
            rng = random.Random(77)
            self._clouds = [
                [rng.uniform(-300, 300), rng.uniform(-300, 300),
                 rng.uniform(0.7, 1.4), rng.uniform(0, math.pi*2)]
                for _ in range(n)
            ]
        spd = self.env['cloud_speed']
        for c in self._clouds:
            c[0] += spd * 0.15
            if c[0] > 400: c[0] -= 800

    # ── 렌더링 ────────────────────────────────────────────────────────────────
    def render(self):
        bt = self.env['sky_bot']
        glClearColor(bt[0], bt[1], bt[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        self.set_camera()

        # GL 안개 설정
        fd = self.env['fog_density']
        sb = self.env['sky_bot']
        if fd > 0.001:
            glEnable(GL_FOG)
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, [sb[0], sb[1], sb[2], 1.0])
            glFogf(GL_FOG_DENSITY, fd * 0.012)
        else:
            glDisable(GL_FOG)

        # ① 하늘 그라디언트 + 별
        self._draw_sky()

        # ② 불투명 지면·구조물·발사대
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        self._draw_ground()
        for st in self.placed_st: st.draw(self.selected is st)
        for fw in self.placed_fw: fw.draw(self.selected is fw)
        self._draw_cursor_preview()
        self._draw_clouds()
        glDisable(GL_DEPTH_TEST)

        # ② 파티클·로켓 (가산 블렌딩)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        self._draw_rockets()
        self._draw_particles()

        # ③ HUD
        self._draw_hud()
        pygame.display.flip()

    def _draw_sky(self):
        """하늘 그라디언트 돔 + 별"""
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        ex, ez = self._eye_x, self._eye_z
        R = 900.0

        top = self.env['sky_top']
        bot = self.env['sky_bot']

        # 수평 방향 16등분 그라디언트 기둥
        segs = 32
        glBegin(GL_QUAD_STRIP)
        for i in range(segs + 1):
            a = 2 * math.pi * i / segs
            sx, sz = math.cos(a) * R, math.sin(a) * R
            glColor3f(bot[0], bot[1], bot[2])
            glVertex3f(ex + sx, GROUND_Y, ez + sz)
            glColor3f(top[0], top[1], top[2])
            glVertex3f(ex + sx, GROUND_Y + R * 0.9, ez + sz)
        glEnd()

        # 천장
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(top[0], top[1], top[2])
        glVertex3f(ex, GROUND_Y + R * 0.9, ez)
        for i in range(segs + 1):
            a = 2 * math.pi * i / segs
            glVertex3f(ex + math.cos(a) * R, GROUND_Y + R * 0.9, ez + math.sin(a) * R)
        glEnd()

        # 별
        n_stars = self.env['stars']
        if n_stars > 0:
            if len(self._stars) != n_stars:
                rng = random.Random(42)
                self._stars = []
                for _ in range(n_stars):
                    a1 = rng.uniform(0, 2 * math.pi)
                    a2 = rng.uniform(0.05, math.pi / 2)
                    self._stars.append((math.cos(a1) * math.cos(a2),
                                        math.sin(a2),
                                        math.sin(a1) * math.cos(a2)))
            glPointSize(2.0)
            glBegin(GL_POINTS)
            for sx, sy, sz in self._stars:
                bri = random.uniform(0.7, 1.0) if n_stars < 100 else 0.9
                glColor3f(bri, bri, bri)
                glVertex3f(ex + sx * R * 0.95, GROUND_Y + sy * R * 0.88, ez + sz * R * 0.95)
            glEnd()
            glPointSize(1.0)

        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

    def _draw_clouds(self):
        if not self._clouds: return
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        ch = GROUND_Y + self.env['cloud_height']
        sz = self.env['cloud_size']
        for cx, cz, csz, _ in self._clouds:
            r = csz * sz
            for ox, oz, pr in [(0,0,r*8),(r*5,r*2,r*6),(-(r*5),r*1,r*6),(r*2,-(r*3),r*5)]:
                px, pz = cx+ox, cz+oz
                segs = 14
                glBegin(GL_TRIANGLE_FAN)
                glColor4f(1, 1, 1, 0.55)
                glVertex3f(px, ch, pz)
                glColor4f(1, 1, 1, 0.0)
                for i in range(segs+1):
                    a = 2*math.pi*i/segs
                    glVertex3f(px+math.cos(a)*pr, ch, pz+math.sin(a)*pr)
                glEnd()
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

    def _draw_ground(self):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

        ex, ez  = self._eye_x, self._eye_z
        FAR     = 1000
        GRID    = 4
        THICK   = 20

        gc = self.env['ground']
        g1 = self.env['grid']
        g2 = self.env['grid2']
        sb = self.env['sky_bot']

        # ── 베이스 평면 (far clip 전체) ───────────────────────────────────────
        x0 = math.floor((ex - FAR) / THICK) * THICK
        x1 = math.ceil ((ex + FAR) / THICK) * THICK
        z0 = math.floor((ez - FAR) / THICK) * THICK
        z1 = math.ceil ((ez + FAR) / THICK) * THICK
        glBegin(GL_QUADS)
        glColor4f(gc[0], gc[1], gc[2], 1.0)
        glVertex3f(x0, GROUND_Y, z1)
        glVertex3f(x1, GROUND_Y, z1)
        glVertex3f(x1, GROUND_Y, z0)
        glVertex3f(x0, GROUND_Y, z0)
        glEnd()

        # ── 타일 디테일 (20유닛 크기, 명도 ±3%, 근거리 100유닛 내) ──────────
        if self.env['tile_detail']:
            TS = 20   # 타일 크기 — 눈에 잘 안 띄는 크기
            TR = 100
            tx0t = int(math.floor((ex - TR) / TS)) * TS
            tx1t = int(math.ceil ((ex + TR) / TS)) * TS
            tz0t = int(math.floor((ez - TR) / TS)) * TS
            tz1t = int(math.ceil ((ez + TR) / TS)) * TS
            glBegin(GL_QUADS)
            xi = tx0t
            while xi < tx1t:
                zi = tz0t
                while zi < tz1t:
                    chk = 0.97 if ((xi // TS + zi // TS) % 2) else 1.0
                    r = min(1.0, gc[0] * chk)
                    g = min(1.0, gc[1] * chk)
                    b = min(1.0, gc[2] * chk)
                    glColor4f(r, g, b, 1.0)
                    glVertex3f(xi,    GROUND_Y+0.01, zi+TS)
                    glVertex3f(xi+TS, GROUND_Y+0.01, zi+TS)
                    glVertex3f(xi+TS, GROUND_Y+0.01, zi)
                    glVertex3f(xi,    GROUND_Y+0.01, zi)
                    zi += TS
                xi += TS
            glEnd()

        # ── 지평선 안개 오버레이 (안개 설정 > 0일 때만) ──────────────────────
        fd = self.env['fog_density']
        if fd > 0.01:
            ATM_R = FAR * 0.85
            segs  = 48
            alpha = min(1.0, fd * 2.0)
            glBegin(GL_TRIANGLE_FAN)
            glColor4f(sb[0], sb[1], sb[2], 0.0)
            glVertex3f(ex, GROUND_Y+0.3, ez)
            glColor4f(sb[0], sb[1], sb[2], alpha)
            for i in range(segs+1):
                a = 2*math.pi*i/segs
                glVertex3f(ex+math.cos(a)*ATM_R, GROUND_Y+0.3, ez+math.sin(a)*ATM_R)
            glEnd()

        # ── 격자선 ────────────────────────────────────────────────────────────
        if self.env['show_grid']:
            VIEW = 200
            gx0 = math.floor((ex-VIEW)/GRID)*GRID; gx1 = math.ceil((ex+VIEW)/GRID)*GRID
            gz0 = math.floor((ez-VIEW)/GRID)*GRID; gz1 = math.ceil((ez+VIEW)/GRID)*GRID
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glColor4f(g1[0], g1[1], g1[2], 0.9)
            xi = gx0
            while xi <= gx1:
                glVertex3f(xi, GROUND_Y+0.05, gz0); glVertex3f(xi, GROUND_Y+0.05, gz1); xi += GRID
            zi = gz0
            while zi <= gz1:
                glVertex3f(gx0, GROUND_Y+0.05, zi); glVertex3f(gx1, GROUND_Y+0.05, zi); zi += GRID
            glEnd()

            bx0 = math.floor((ex-FAR)/THICK)*THICK; bx1 = math.ceil((ex+FAR)/THICK)*THICK
            bz0 = math.floor((ez-FAR)/THICK)*THICK; bz1 = math.ceil((ez+FAR)/THICK)*THICK
            glLineWidth(1.8)
            glBegin(GL_LINES)
            glColor4f(g2[0], g2[1], g2[2], 1.0)
            xi = bx0
            while xi <= bx1:
                glVertex3f(xi, GROUND_Y+0.08, bz0); glVertex3f(xi, GROUND_Y+0.08, bz1); xi += THICK
            zi = bz0
            while zi <= bz1:
                glVertex3f(bx0, GROUND_Y+0.08, zi); glVertex3f(bx1, GROUND_Y+0.08, zi); zi += THICK
            glEnd()

        glLineWidth(1.0)
        glDisable(GL_DEPTH_TEST)

    def _draw_cursor_preview(self):
        if self.cursor_pos is None: return
        x,_,z = self.cursor_pos
        if self.mode == MODE_FW:
            glLineWidth(1.5)
            gl_ground_ring(x, z, 2.0, (1.0,1.0,0.5), 0.8)
            pc = PALETTES[self.cur_pal][0]
            gl_ground_ring(x, z, 1.4, pc, 0.6)
            glLineWidth(1.0)
        elif self.mode == MODE_ST:
            glLineWidth(1.5)
            gl_ground_ring(x, z, 5*self.cur_scale, (0.5,0.8,1.0), 0.7)
            glLineWidth(1.0)

    def _draw_rockets(self):
        for r in self.rockets:
            if len(r.trail) > 1:
                n = len(r.trail)
                # ── 외부 불꽃 코어 트레일 (두꺼운 황금색)
                glLineWidth(4.0)
                glBegin(GL_LINE_STRIP)
                for i,(tx,ty,tz) in enumerate(r.trail):
                    a = (i/n) ** 0.5
                    glColor4f(1.0, 0.72, 0.18, a * 0.85)
                    glVertex3f(tx,ty,tz)
                glEnd()
                # ── 중간 주황 레이어
                glLineWidth(2.2)
                glBegin(GL_LINE_STRIP)
                for i,(tx,ty,tz) in enumerate(r.trail):
                    a = (i/n) ** 0.45
                    glColor4f(1.0, 0.55, 0.10, a * 0.70)
                    glVertex3f(tx,ty,tz)
                glEnd()
                # ── 내부 흰색 고온 코어
                glLineWidth(1.0)
                glBegin(GL_LINE_STRIP)
                for i,(tx,ty,tz) in enumerate(r.trail):
                    a = (i/n) ** 0.35
                    glColor4f(1.0, 0.96, 0.85, a * 0.90)
                    glVertex3f(tx,ty,tz)
                glEnd()
            # ── 헤드 글로우 (3겹)
            glPointSize(22.0)
            glBegin(GL_POINTS)
            glColor4f(1.0, 0.60, 0.15, 0.18); glVertex3f(r.x,r.y,r.z)
            glEnd()
            glPointSize(11.0)
            glBegin(GL_POINTS)
            glColor4f(1.0, 0.80, 0.35, 0.55); glVertex3f(r.x,r.y,r.z)
            glEnd()
            glPointSize(4.5)
            glBegin(GL_POINTS)
            glColor4f(1.0, 1.0, 0.92, 1.00); glVertex3f(r.x,r.y,r.z)
            glEnd()

    def _draw_particles(self):
        if not self.particles: return
        ps = self.env['particle_size']

        # cache: (alpha, hot, r,g,b, x,y,z, spark, size)
        cache = []
        for p in self.particles:
            a = p.life / p.max_life
            if a < 0.15:
                a = (a / 0.15) ** 1.6
            if p.strobe:
                a *= max(0.0, math.sin(p.life * 0.52))
            if a < 0.03:
                continue
            a_raw = p.life / p.max_life
            if p.hot > 0.0 and a_raw > (1.0 - p.hot):
                h = min(1.0, ((a_raw - (1.0 - p.hot)) / p.hot) * 1.2)
            else:
                h = 0.0
            cache.append((a, h, p.r, p.g, p.b, p.x, p.y, p.z, p.spark, p.size))

        if not cache:
            return

        # p.size → 5단계 버킷 (0‥4)으로 분류해 per-bucket glPointSize 호출
        # 버킷 경계:  sz<4 / 4-8 / 8-14 / 14-20 / 20+
        THRESHOLDS = (4, 8, 14, 20)
        CORE_M     = (1.0,  1.8,  3.2,  5.5,  8.0 )  # core point-size multiplier
        GLOW_M     = (2.5,  4.5,  9.0, 15.0, 22.0 )  # halo point-size multiplier
        MEGA_M     = (5.0,  9.0, 16.0, 26.0, 38.0 )  # mega outer glow

        buckets = [[] for _ in range(5)]
        for item in cache:
            sz = item[9]
            bk = 4
            for i, t in enumerate(THRESHOLDS):
                if sz < t:
                    bk = i
                    break
            buckets[bk].append(item)

        # ── 패스 0: 메가 외부 글로우 (크고 매우 부드러운 빛번짐) ──────────────
        for bk in range(4, -1, -1):
            items = buckets[bk]
            if not items: continue
            glPointSize(max(5.0, ps * MEGA_M[bk]))
            glBegin(GL_POINTS)
            for (a, h, r, g, b, x, y, z, spark, sz) in items:
                if spark:
                    glColor4f(1.0, 0.60, 0.05, a * 0.09)
                else:
                    gr = min(1.0, r + (1.0-r)*h*0.75)
                    gg = min(1.0, g + (1.0-g)*h*0.55)
                    gb = min(1.0, b*0.60 + h*0.10)
                    glColor4f(gr, gg, gb, a * 0.18)
                glVertex3f(x, y, z)
            glEnd()

        # ── 패스 A: 내부 글로우 헤일로 ─────────────────────────────────────────
        for bk in range(4, -1, -1):
            items = buckets[bk]
            if not items: continue
            glPointSize(max(3.0, ps * GLOW_M[bk]))
            glBegin(GL_POINTS)
            for (a, h, r, g, b, x, y, z, spark, sz) in items:
                if spark:
                    glColor4f(1.0, 0.70, 0.10, a * 0.30)
                else:
                    gr = min(1.0, r + (1.0-r)*h*0.85)
                    gg = min(1.0, g + (1.0-g)*h*0.70)
                    gb = min(1.0, b*0.80 + h*0.20)
                    glColor4f(gr, gg, gb, a * 0.45)
                glVertex3f(x, y, z)
            glEnd()

        # ── 패스 B: 코어 ─────────────────────────────────────────────────────
        for bk in range(4, -1, -1):
            items = buckets[bk]
            if not items: continue
            glPointSize(max(1.5, ps * CORE_M[bk]))
            glBegin(GL_POINTS)
            for (a, h, r, g, b, x, y, z, spark, sz) in items:
                if spark:
                    glColor4f(1.0, 0.80 + h*0.20, 0.18*a, a * 1.0)
                else:
                    cr = min(1.0, r + (1.0-r)*h)
                    cg = min(1.0, g + (1.0-g)*h*0.90)
                    cb = min(1.0, b + (1.0-b)*h*0.65)
                    glColor4f(cr, cg, cb, a * 1.0)
                glVertex3f(x, y, z)
            glEnd()

        # ── 패스 C: 화이트핫 심지 (hot 파티클만, 가장 작고 가장 밝음) ─────────
        for bk in range(4, -1, -1):
            items = buckets[bk]
            if not items: continue
            glPointSize(max(1.0, ps * CORE_M[bk] * 0.45))
            glBegin(GL_POINTS)
            for (a, h, r, g, b, x, y, z, spark, sz) in items:
                if h > 0.15:
                    glColor4f(1.0, 0.98, 0.92, h * a * 1.0)
                    glVertex3f(x, y, z)
            glEnd()

    # ── HUD (pygame surface → GL 텍스처) ─────────────────────────────────────
    def _draw_hud(self):
        surf = pygame.Surface((W, H), pygame.SRCALPHA)

        # ── 상단 모드 바 ──────────────────────────────────────────────────────
        self._draw_topbar(surf)

        # ── 발사 중 알림 ( pill) ────────────────────────────────
        if self.seq_active:
            elapsed = time.time()-self.seq_start
            fired = sum(1 for fw in self.placed_fw if fw.fired)
            msg = f"▶  Playing  {fired} / {len(self.placed_fw)}   {elapsed:.1f}s"
            s = self.font_sm.render(msg, True, (220,220,220))
            pw, ph = s.get_width()+28, 30
            bx, by = W//2-pw//2, 50
            pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pill.fill((37,37,37,230))
            pygame.draw.rect(pill,(0,149,232,200),(0,0,pw,ph),1)
            surf.blit(pill, (bx, by))
            surf.blit(s, (bx+14, by+7))

        # ── 폭죽 커스텀 패널 ────────────────────────────────────────────────
        if self.fw_panel_open:
            try:
                self._draw_fw_panel(surf)
            except Exception as e:
                print(f"[FW panel error] {e}")
                import traceback; traceback.print_exc()

        # ── 환경 설정 패널 ──────────────────────────────────────────────────
        if self.env_panel_open:
            self._draw_env_panel(surf)

        # ── DAW 타임라인 패널 ────────────────────────────────────────────────
        self._draw_daw(surf)

        # GL 오버레이
        self._blit_surface(surf)

    def _draw_topbar(self, surf):
        # ──  Studio 상단 툴바 ──────────────────────────────────────────
        bar_h = 42
        # 배경 (진한 회색)
        bg = pygame.Surface((W, bar_h), pygame.SRCALPHA)
        bg.fill((37, 37, 37, 252))
        surf.blit(bg, (0, 0))
        pygame.draw.line(surf, (60, 60, 60), (0, bar_h-1), (W, bar_h-1), 1)

        # 왼쪽 로고 영역
        logo = self.font_lg.render("Fireworks Studio", True, (220, 220, 220))
        surf.blit(logo, (14, 11))
        lw = logo.get_width()
        pygame.draw.line(surf, (65,65,65), (lw+22, 6), (lw+22, bar_h-6), 1)

        # 모드 탭 버튼 (클릭 영역 저장)
        sections = [
            ("1  Camera",   MODE_CAM),
            ("2  Firework", MODE_FW),
            ("3  Model",    MODE_ST),
            ("4  Select",   MODE_SEL),
        ]
        BLUE   = (0, 149, 232)
        tx = lw + 34
        self._topbar_rects = []
        for label, m in sections:
            is_cur = (self.mode == m)
            bw = self.font_sm.size(label)[0] + 22
            self._topbar_rects.append((pygame.Rect(tx, 0, bw, bar_h), m))
            if is_cur:
                btn = pygame.Surface((bw, bar_h), pygame.SRCALPHA)
                btn.fill((55, 55, 55, 255))
                surf.blit(btn, (tx, 0))
                pygame.draw.line(surf, BLUE, (tx, bar_h-2), (tx+bw, bar_h-2), 2)
            tcol = (220,220,220) if is_cur else (155,155,155)
            ts = self.font_sm.render(label, True, tcol)
            surf.blit(ts, (tx + 11, 14))
            tx += bw + 2

        # 오른쪽 버튼들
        enter_col = (0,149,232) if not self.seq_active else (232,60,60)
        enter_txt = "▶  Play" if not self.seq_active else "■  Stop"
        env_col   = (0,200,160) if self.env_panel_open else (130,130,130)
        fw_col    = (0,149,232) if self.fw_panel_open  else (130,130,130)
        right_items = [
            (enter_txt,       enter_col, True,  'play'),
            ("*  FW커스텀",    fw_col,    True,  'fw'),
            ("⚙  Env",        env_col,   True,  'env'),
            ("F5  Reset",     (155,155,155), False, None),
            ("ESC  Quit",     (120,120,120), False, None),
        ]

        # 힌트 (현재 모드) — 오른쪽 버튼 영역과 겹치지 않도록 클리핑
        hints = {
            MODE_CAM: "RMB: Rotate   WASD: Move   Q/E: Up/Down   Scroll: Zoom   MMB: Pan   F: Reset",
            MODE_FW:  "Click ground to place  |  Use picker below to configure",
            MODE_ST:  "Click ground to place  |  Use picker below to configure",
            MODE_SEL: "Click object to select  |  Edit properties in picker below",
        }
        right_total_w = sum(self.font_sm.size(rt)[0] + 26 for rt, _, _, _ in right_items) + 10
        hint_x = tx + 16
        hint_max_w = W - right_total_w - hint_x - 8
        if hint_max_w > 30:
            hs = self.font_xs.render(hints[self.mode], True, (130,130,130))
            old_clip = surf.get_clip()
            surf.set_clip(pygame.Rect(hint_x, 0, hint_max_w, bar_h))
            surf.blit(hs, (hint_x, 15))
            surf.set_clip(old_clip)
        rx = W - 10
        self._env_btn_topbar = None
        self._fw_btn_topbar  = None
        for rtxt, rcol, is_btn, tag in reversed(right_items):
            rs = self.font_sm.render(rtxt, True, rcol)
            bw2 = rs.get_width() + 18
            rx -= bw2 + 8
            if is_btn:
                bb = pygame.Surface((bw2, 26), pygame.SRCALPHA)
                bb.fill((*rcol, 40))
                surf.blit(bb, (rx, 8))
                pygame.draw.rect(surf, (*rcol, 160), (rx, 8, bw2, 26), 1)
            surf.blit(rs, (rx+9, 14))
            if tag == 'env':
                self._env_btn_topbar = pygame.Rect(rx, 8, bw2, 26)
            elif tag == 'fw':
                self._fw_btn_topbar = pygame.Rect(rx, 8, bw2, 26)

    # ── 폭죽 커스텀 패널 ─────────────────────────────────────────────────────
    def _fw_target(self):
        """편집 대상 반환 (선택된 FW or None=defaults)"""
        if isinstance(self.selected, PlacedFirework):
            return self.selected
        return None

    # PlacedFirework 속성명 → Game cur_ 속성명 매핑
    _FW_KEY = {'shape_idx': 'cur_shape', 'pal_idx': 'cur_pal',
               'use_custom_col': 'cur_use_cc'}

    def _fw_get(self, key):
        t = self._fw_target()
        if t: return getattr(t, key)
        return getattr(self, self._FW_KEY.get(key, 'cur_' + key))

    def _fw_set(self, key, val):
        t = self._fw_target()
        if t: setattr(t, key, val)
        else: setattr(self, self._FW_KEY.get(key, 'cur_' + key), val)

    def _draw_fw_panel(self, surf):
        PX, PY  = 0, 42
        PW, PH  = FW_PANEL_W, H - 42 - TL_H
        C_BG    = (22, 24, 28, 248)
        C_BORDER= (55, 60, 65)
        C_BLUE  = (0, 149, 232)
        C_GREEN = (0, 200, 140)
        C_TEXT  = (210, 210, 210)
        C_DIM   = (110, 110, 110)

        panel = pygame.Surface((PW, PH), pygame.SRCALPHA)
        panel.fill(C_BG)
        pygame.draw.line(panel, C_BORDER, (PW-1, 0), (PW-1, PH), 1)

        self._fw_slider_rects = []
        self._fw_btn_rects    = []

        # 제목
        t = self._fw_target()
        title_txt = "폭죽 커스텀 — 선택됨" if t else "폭죽 커스텀 — 기본값"
        ts = self.font_xs.render(title_txt, True, C_DIM)
        panel.blit(ts, (10, 6))

        # 탭  0=모양  1=세부  2=속성  3=색상  4=공유
        tabs = ['모양', '세부', '속성', '색상', '공유']
        TH = 32; tw = PW // len(tabs)
        for i, tb in enumerate(tabs):
            act = (self.fw_panel_tab == i)
            pygame.draw.rect(panel, (38,42,48) if act else (28,30,34), (i*tw, 18, tw, TH))
            if act:
                pygame.draw.line(panel, C_BLUE, (i*tw, 18+TH-2), (i*tw+tw, 18+TH-2), 2)
            tc2 = C_TEXT if act else C_DIM
            ts2 = self.font_xs.render(tb, True, tc2)
            panel.blit(ts2, (i*tw+tw//2-ts2.get_width()//2, 18+TH//2-ts2.get_height()//2))
            self._fw_btn_rects.append((pygame.Rect(PX+i*tw, PY+18, tw, TH), 'tab', i))
        pygame.draw.line(panel, C_BORDER, (0, 50), (PW, 50), 1)

        cy = 58

        def btn_label(text, y, color=C_DIM):
            s = self.font_xs.render(text, True, color)
            panel.blit(s, (10, y))
            return y + s.get_height() + 3

        def fw_slider(key, text, y, vmin, vmax, is_int=False):
            val = self._fw_get(key)
            ls = self.font_xs.render(text, True, C_DIM)
            panel.blit(ls, (10, y+3))
            TX, TW = 90, PW - 90 - 44
            norm = max(0.0, min(1.0, (val-vmin)/(max(vmax-vmin,1e-6))))
            pygame.draw.rect(panel, (45,48,52), (TX, y+5, TW, 14), border_radius=3)
            fw2 = int(norm*TW)
            if fw2 > 0:
                pygame.draw.rect(panel, C_BLUE, (TX, y+5, fw2, 14), border_radius=3)
            pygame.draw.circle(panel, (220,220,220), (TX+fw2, y+12), 6)
            disp = str(int(val)) if is_int else f"{val:.2f}"
            vs2 = self.font_xs.render(disp, True, C_TEXT)
            panel.blit(vs2, (TX+TW+6, y+3))
            self._fw_slider_rects.append(
                (pygame.Rect(PX+TX, PY+y, TW, 22), key, None, vmin, vmax, is_int))
            return y + 28

        def cc_slider(key, ci, text, y):
            val = self._fw_get(key)[ci]
            ls = self.font_xs.render(text, True, C_DIM)
            panel.blit(ls, (12, y+3))
            TX, TW = 32, PW - 32 - 44
            norm = max(0.0, min(1.0, val))
            pygame.draw.rect(panel, (45,48,52), (TX, y+5, TW, 12), border_radius=3)
            fw2 = int(norm*TW)
            if fw2 > 0:
                pygame.draw.rect(panel, C_BLUE, (TX, y+5, fw2, 12), border_radius=3)
            pygame.draw.circle(panel, (210,210,210), (TX+fw2, y+11), 5)
            disp = f"{val:.2f}"
            vs2 = self.font_xs.render(disp, True, C_TEXT)
            panel.blit(vs2, (TX+TW+6, y+2))
            self._fw_slider_rects.append(
                (pygame.Rect(PX+TX, PY+y, TW, 20), key, ci, 0.0, 1.0, False))
            return y + 24

        # ── 탭 콘텐츠 ────────────────────────────────────────────────────────
        if self.fw_panel_tab == 0:  # 모양
            COLS_P = 3; BW_P = (PW - 16 - (COLS_P-1)*4) // COLS_P; BH_P = 26
            for i in range(len(SHAPE_NAMES)):
                ci2, ri2 = i % COLS_P, i // COLS_P
                bx2 = 8 + ci2*(BW_P+4)
                by2 = cy + ri2*(BH_P+4)
                act2 = (i == self._fw_get('shape_idx'))
                pygame.draw.rect(panel, C_BLUE if act2 else (45,48,55),
                                 (bx2, by2, BW_P, BH_P), border_radius=4)
                pygame.draw.rect(panel, C_BORDER, (bx2, by2, BW_P, BH_P), 1, border_radius=4)
                ns2 = self.font_xs.render(SHAPE_NAMES[i], True,
                                          C_TEXT if act2 else C_DIM)
                panel.blit(ns2, (bx2+BW_P//2-ns2.get_width()//2,
                                 by2+BH_P//2-ns2.get_height()//2))
                self._fw_btn_rects.append(
                    (pygame.Rect(PX+bx2, PY+by2, BW_P, BH_P), 'shape', i))

        elif self.fw_panel_tab == 1:  # 세부 (모양 파라미터)
            cy = btn_label("── 퍼짐 / 방향", cy, C_DIM)
            cy = fw_slider('spread',    "퍼짐 폭",  cy, 0.2, 2.5)
            cy = fw_slider('wobble',    "흔들림",   cy, 0.0, 2.5)
            cy = fw_slider('lift',      "상승 편향", cy, -1.0, 2.5)
            cy = btn_label("── 꼬리 / 이펙트", cy+4, C_DIM)
            cy = fw_slider('tail_len',  "꼬리 길이", cy, 0.2, 3.5)
            cy = fw_slider('secondary', "보조 이펙트", cy, 0.0, 2.5)
            cy = btn_label("── 팔 수 (야자·달리아·별꽃)", cy+4, C_DIM)
            cy = fw_slider('arm_count', "팔 수 (0=기본)", cy, 0, 20, is_int=True)

        elif self.fw_panel_tab == 2:  # 속성
            cy = btn_label("── 발사 / 폭발", cy, C_DIM)
            cy = fw_slider('launch_h',   "발사 높이", cy,  5.0, 500.0)
            cy = fw_slider('burst_size', "폭발 크기", cy,  0.2,   3.0)
            cy = btn_label("── 파티클", cy+4, C_DIM)
            cy = fw_slider('part_mul',   "파티클 수", cy,  0.2,   3.0)
            cy = fw_slider('grav_mul',   "중력",     cy,  0.1,   4.0)
            cy = fw_slider('drag_mul',   "드래그",   cy,  0.3,   2.0)

        elif self.fw_panel_tab == 3:  # 색상
            # 팔레트 / 커스텀 토글
            use_cc = self._fw_get('use_custom_col')
            for ii, lbl in enumerate(['팔레트', '커스텀']):
                act3 = (bool(use_cc) == bool(ii))
                bx3 = 8 + ii*((PW-22)//2+6)
                pygame.draw.rect(panel, C_GREEN if act3 else (45,48,55),
                                 (bx3, cy, (PW-22)//2, 26), border_radius=5)
                ts3 = self.font_xs.render(lbl, True, C_TEXT)
                panel.blit(ts3, (bx3+(PW-22)//4-ts3.get_width()//2, cy+6))
                self._fw_btn_rects.append(
                    (pygame.Rect(PX+bx3, PY+cy, (PW-22)//2, 26), 'cc_toggle', ii))
            cy += 34

            if not use_cc:
                cy = btn_label("── 팔레트", cy, C_DIM)
                sw = 28
                cur_pal = self._fw_get('pal_idx')
                for ii in range(len(PALETTES)):
                    r2,g2,b2 = (int(c*255) for c in PALETTES[ii][0])
                    pygame.draw.rect(panel, (r2,g2,b2), (8+ii*(sw+4), cy, sw, sw), border_radius=4)
                    if ii == cur_pal:
                        pygame.draw.rect(panel, C_BLUE, (6+ii*(sw+4), cy-2, sw+4, sw+4), 2, border_radius=5)
                    self._fw_btn_rects.append(
                        (pygame.Rect(PX+8+ii*(sw+4), PY+cy, sw, sw), 'pal', ii))
            else:
                cy = btn_label("── 커스텀 색 3가지", cy, C_DIM)
                for ci3, cname in enumerate(['색 1', '색 2', '색 3']):
                    cy = btn_label(cname, cy, C_TEXT)
                    cy = cc_slider('custom_cols', ci3*3+0 if False else ci3, 'R', cy)
                    # Actually need per-component: restructure
                    pass
                # Simpler: draw 3 color groups
                cy -= 14  # undo last btn_label
                cc = self._fw_get('custom_cols')
                for ci3 in range(3):
                    r3,g3,b3 = int(cc[ci3][0]*255), int(cc[ci3][1]*255), int(cc[ci3][2]*255)
                    pygame.draw.rect(panel, (r3,g3,b3), (PW-34, cy+2, 24, 20), border_radius=3)
                    cy = btn_label(f"─ 색{ci3+1}", cy, C_TEXT)
                    for ch_i, ch_name in enumerate(['R','G','B']):
                        val = cc[ci3][ch_i]
                        ls3 = self.font_xs.render(ch_name, True, C_DIM)
                        panel.blit(ls3, (12, cy+3))
                        TX3, TW3 = 28, PW-28-44
                        norm3 = max(0.0, min(1.0, val))
                        pygame.draw.rect(panel, (45,48,52), (TX3, cy+5, TW3, 12), border_radius=3)
                        fw3 = int(norm3*TW3)
                        if fw3>0: pygame.draw.rect(panel, C_BLUE, (TX3,cy+5,fw3,12), border_radius=3)
                        pygame.draw.circle(panel,(210,210,210),(TX3+fw3, cy+11),5)
                        vs3 = self.font_xs.render(f"{val:.2f}", True, C_TEXT)
                        panel.blit(vs3, (TX3+TW3+6, cy+2))
                        self._fw_slider_rects.append(
                            (pygame.Rect(PX+TX3, PY+cy, TW3, 20), 'custom_cols', ci3*3+ch_i, 0.0, 1.0, False))
                        cy += 22
                    cy += 4

        elif self.fw_panel_tab == 4:  # 공유
            t2 = self._fw_target()
            cy = btn_label("── 공유 코드", cy, C_DIM)

            if t2:
                code = fw_to_code(t2)
                # 코드 표시 (3줄로 나눠서)
                chunk = 38
                lines = [code[i:i+chunk] for i in range(0, len(code), chunk)]
                for ln in lines[:4]:
                    ls4 = self.font_xs.render(ln, True, (160,200,160))
                    panel.blit(ls4, (10, cy)); cy += 16
                cy += 4

                # 복사 버튼
                pygame.draw.rect(panel, (0,100,60), (10, cy, 120, 28), border_radius=5)
                cs4 = self.font_xs.render("클립보드 복사", True, C_TEXT)
                panel.blit(cs4, (10+60-cs4.get_width()//2, cy+7))
                self._fw_btn_rects.append((pygame.Rect(PX+10, PY+cy, 120, 28), 'copy_code', None))
                cy += 36
            else:
                cy = btn_label("(폭죽을 선택하세요)", cy+4, C_DIM)
                cy += 10

            # 불러오기
            pygame.draw.rect(panel, (60,60,120), (10, cy, 120, 28), border_radius=5)
            is4 = self.font_xs.render("코드 붙여넣기", True, C_TEXT)
            panel.blit(is4, (10+60-is4.get_width()//2, cy+7))
            self._fw_btn_rects.append((pygame.Rect(PX+10, PY+cy, 120, 28), 'paste_code', None))
            cy += 36

            if self._fw_import_active:
                pygame.draw.rect(panel, (35,38,45), (8, cy, PW-16, 28), border_radius=4)
                pygame.draw.rect(panel, C_BLUE, (8, cy, PW-16, 28), 1, border_radius=4)
                disp_buf = self._fw_import_buf[-36:] if len(self._fw_import_buf)>36 else self._fw_import_buf
                bs5 = self.font_xs.render(disp_buf + "▌", True, C_TEXT)
                panel.blit(bs5, (12, cy+7))
                cy += 34
                hint5 = self.font_xs.render("Enter=적용  Esc=취소", True, C_DIM)
                panel.blit(hint5, (10, cy))

        surf.blit(panel, (PX, PY))

    def _fw_panel_click(self, mx, my):
        for rect, action, val in self._fw_btn_rects:
            if rect.collidepoint(mx, my):
                if action == 'tab':
                    self.fw_panel_tab = val
                elif action == 'shape':
                    self._fw_set('shape_idx', val)
                elif action == 'pal':
                    self._fw_set('pal_idx', val)
                elif action == 'cc_toggle':
                    self._fw_set('use_custom_col', bool(val))
                elif action == 'copy_code':
                    t3 = self._fw_target()
                    if t3:
                        self._clipboard_copy(fw_to_code(t3))
                elif action == 'paste_code':
                    self._fw_import_active = True
                    self._fw_import_buf = self._clipboard_get_text()
                return
        for rect, key, comp, vmin, vmax, is_int in self._fw_slider_rects:
            if rect.collidepoint(mx, my):
                self._fw_slider_drag = (key, comp, rect.x, rect.width, vmin, vmax, is_int)
                self._fw_slider_update(mx)
                return

    def _fw_slider_update(self, mx):
        if not self._fw_slider_drag: return
        key, comp, rx, rw, vmin, vmax, is_int = self._fw_slider_drag
        norm = max(0.0, min(1.0, (mx - rx) / rw))
        val  = vmin + norm * (vmax - vmin)
        if is_int: val = int(round(val))
        if comp is None:
            self._fw_set(key, val)
        else:
            # custom_cols 슬라이더: comp = ci*3 + ch
            ci3 = comp // 3; ch3 = comp % 3
            cur = [list(c) for c in self._fw_get('custom_cols')]
            cur[ci3][ch3] = round(val, 3)
            self._fw_set('custom_cols', cur)

    def _fw_import_apply(self):
        props = code_to_fw_props(self._fw_import_buf.strip())
        if not props:
            self._fw_import_active = False
            return
        keys = [('shape_idx','sh'),('pal_idx','pl'),('delay','dl'),
                ('burst_size','bs'),('part_mul','pm'),('grav_mul','gm'),
                ('drag_mul','dm'),('launch_h','lh'),('use_custom_col','uc'),
                ('custom_cols','cc'),
                ('spread','sp'),('tail_len','tl'),('wobble','wb'),
                ('secondary','sc'),('arm_count','ac'),('lift','lf')]
        for attr, k in keys:
            if k in props:
                v = props[k]
                if k == 'uc': v = bool(v)
                if k == 'ac': v = int(v)
                self._fw_set(attr, v)
        self._fw_import_active = False
        self._fw_import_buf    = ''

    def _clipboard_copy(self, text):
        try:
            import tkinter as tk
            r = tk.Tk(); r.withdraw()
            r.clipboard_clear(); r.clipboard_append(text)
            r.after(200, r.destroy); r.mainloop()
        except Exception: pass

    def _clipboard_get_text(self):
        try:
            import tkinter as tk
            r = tk.Tk(); r.withdraw()
            t5 = r.clipboard_get(); r.destroy()
            return t5
        except Exception: return ''

    # ── 환경 설정 패널 ────────────────────────────────────────────────────────
    def _draw_env_panel(self, surf):
        PX  = W - ENV_PANEL_W
        PY  = 42
        PH  = H - 42 - TL_H   # 타임라인 위까지
        PW  = ENV_PANEL_W
        C_BG     = (22, 24, 28, 248)
        C_BORDER = (55, 60, 65)
        C_GREEN  = (0, 200, 160)
        C_TEXT   = (210, 210, 210)
        C_DIM    = (110, 110, 110)

        panel = pygame.Surface((PW, PH), pygame.SRCALPHA)
        panel.fill(C_BG)
        pygame.draw.line(panel, C_BORDER, (0, 0), (0, PH), 1)

        self._env_slider_rects = []
        self._env_btn_rects    = []

        # ── 탭 ──────────────────────────────────────────────────────────────
        tabs = ['배경', '하늘', '지면', '구름', '그래픽']
        TH = 34
        tw = PW // len(tabs)
        for i, t in enumerate(tabs):
            active = (self.env_tab == i)
            col = (38, 42, 48, 255) if active else (28, 30, 34, 255)
            pygame.draw.rect(panel, col, (i*tw, 0, tw, TH))
            if active:
                pygame.draw.line(panel, C_GREEN, (i*tw, TH-2), (i*tw+tw, TH-2), 2)
            tc = C_TEXT if active else C_DIM
            ts = self.font_xs.render(t, True, tc)
            panel.blit(ts, (i*tw + tw//2 - ts.get_width()//2, TH//2 - ts.get_height()//2))
            self._env_btn_rects.append((pygame.Rect(PX+i*tw, PY, tw, TH), 'tab', i))
        pygame.draw.line(panel, C_BORDER, (0, TH), (PW, TH), 1)

        cy = TH + 8   # 콘텐츠 시작 y

        def label(text, y, color=C_DIM):
            s = self.font_xs.render(text, True, color)
            panel.blit(s, (10, y))
            return y + s.get_height() + 2

        def slider(key, comp, text, y, vmin, vmax, is_int=False):
            """슬라이더 1줄 그리기, 클릭 영역 등록"""
            val = self.env[key] if comp is None else self.env[key][comp]
            # 레이블
            ls = self.font_xs.render(text, True, C_DIM)
            panel.blit(ls, (10, y+3))
            # 트랙
            TX, TW = 95, PW - 95 - 46
            norm = (val - vmin) / max(vmax - vmin, 1e-6)
            norm = max(0.0, min(1.0, norm))
            pygame.draw.rect(panel, (45,48,52), (TX, y+5, TW, 14), border_radius=3)
            fw = int(norm * TW)
            if fw > 0:
                pygame.draw.rect(panel, C_GREEN, (TX, y+5, fw, 14), border_radius=3)
            # 썸
            tx_thumb = TX + fw
            pygame.draw.circle(panel, (220,220,220), (tx_thumb, y+12), 6)
            # 값
            disp = str(int(val)) if is_int else f"{val:.2f}"
            vs = self.font_xs.render(disp, True, C_TEXT)
            panel.blit(vs, (TX+TW+6, y+3))
            # 클릭 영역 (절대 좌표)
            self._env_slider_rects.append(
                (pygame.Rect(PX+TX, PY+y, TW, 22), key, comp, vmin, vmax, is_int))
            return y + 26

        def color_row(key, text, y):
            """RGB 3-슬라이더 묶음"""
            y = label(f"── {text}", y, C_DIM)
            labels = ['R', 'G', 'B']
            for i in range(3):
                y = slider(key, i, f"  {labels[i]}", y, 0.0, 1.0)
            # 색 미리보기 스와치
            r,g,b = [int(self.env[key][c]*255) for c in range(3)]
            pygame.draw.rect(panel, (r,g,b), (PW-38, y-78, 28, 70), border_radius=4)
            pygame.draw.rect(panel, C_BORDER, (PW-38, y-78, 28, 70), 1, border_radius=4)
            return y + 4

        # ── 탭별 콘텐츠 ─────────────────────────────────────────────────────
        if self.env_tab == 0:  # 배경 프리셋
            cy = label("배경 프리셋  (B키로도 전환)", cy, C_DIM)
            cols, bw, bh = 2, (PW - 24) // 2, 32
            for i, bg in enumerate(BACKGROUNDS):
                col_i, row_i = i % cols, i // cols
                bx = 8 + col_i * (bw + 8)
                by = cy + row_i * (bh + 6)
                active = (self.cur_bg == i)
                bc = C_GREEN if active else (50, 54, 60)
                pygame.draw.rect(panel, bc, (bx, by, bw, bh), border_radius=5)
                if not active:
                    pygame.draw.rect(panel, C_BORDER, (bx, by, bw, bh), 1, border_radius=5)
                ns = self.font_xs.render(bg['name'], True, C_TEXT if active else C_DIM)
                panel.blit(ns, (bx + bw//2 - ns.get_width()//2, by + bh//2 - ns.get_height()//2))
                self._env_btn_rects.append(
                    (pygame.Rect(PX+bx, PY+by, bw, bh), 'bg_preset', i))
            cy += ((len(BACKGROUNDS)+1)//cols) * (bh+6) + 12

            # 별 개수 슬라이더
            cy = label("── 별", cy, C_DIM)
            cy = slider('stars', None, "개수", cy, 0, 600, is_int=True)

        elif self.env_tab == 1:  # 하늘
            cy = color_row('sky_top', '하늘 위 색', cy)
            cy = color_row('sky_bot', '하늘 아래 색', cy)

        elif self.env_tab == 2:  # 지면
            cy = color_row('ground', '지면 색', cy)
            cy = label("── 지면 재질 프리셋", cy, C_DIM)
            cols2, bw2, bh2 = 3, (PW - 28) // 3, 28
            for i, mat in enumerate(TERRAIN_MATERIALS):
                col_i2, row_i2 = i % cols2, i // cols2
                bx2 = 8 + col_i2 * (bw2 + 6)
                by2 = cy + row_i2 * (bh2 + 6)
                gc = tuple(int(x*255) for x in mat['ground'])
                pygame.draw.rect(panel, gc, (bx2, by2, bw2, bh2), border_radius=4)
                pygame.draw.rect(panel, C_BORDER, (bx2, by2, bw2, bh2), 1, border_radius=4)
                ns2 = self.font_xs.render(mat['name'], True, (240,240,240))
                panel.blit(ns2, (bx2+bw2//2-ns2.get_width()//2, by2+bh2//2-ns2.get_height()//2))
                self._env_btn_rects.append(
                    (pygame.Rect(PX+bx2, PY+by2, bw2, bh2), 'terrain', i))
            cy += ((len(TERRAIN_MATERIALS)+2)//cols2) * (bh2+6) + 8
            cy = label("── 격자 색", cy, C_DIM)
            cy = slider('grid',  0, "  R", cy, 0.0, 1.0)
            cy = slider('grid',  1, "  G", cy, 0.0, 1.0)
            cy = slider('grid',  2, "  B", cy, 0.0, 1.0)

        elif self.env_tab == 3:  # 구름
            cy = label("── 구름 설정", cy, C_DIM)
            cy = slider('cloud_count',  None, "개수",  cy,   0,   50, is_int=True)
            cy = slider('cloud_speed',  None, "속도",  cy, 0.0,  5.0)
            cy = slider('cloud_height', None, "높이",  cy, 5.0, 500.0)
            cy = slider('cloud_size',   None, "크기",  cy, 0.3,  5.0)

        elif self.env_tab == 4:  # 그래픽
            cy = label("── 그래픽 설정", cy, C_DIM)
            cy = slider('fog_density',   None, "안개",   cy, 0.0, 1.0)
            cy = slider('particle_size', None, "파티클", cy, 1.0, 8.0)
            cy += 8

            # 격자 토글
            sg = self.env['show_grid']
            gc2 = C_GREEN if sg else (55,58,64)
            pygame.draw.rect(panel, gc2, (10, cy, 130, 28), border_radius=5)
            if not sg:
                pygame.draw.rect(panel, C_BORDER, (10, cy, 130, 28), 1, border_radius=5)
            gs = self.font_xs.render("격자  " + ("ON" if sg else "OFF"), True, C_TEXT)
            panel.blit(gs, (10+65-gs.get_width()//2, cy+7))
            self._env_btn_rects.append((pygame.Rect(PX+10, PY+cy, 130, 28), 'toggle', 'show_grid'))
            cy += 36

            # 타일 디테일 토글
            td = self.env['tile_detail']
            tc2 = C_GREEN if td else (55,58,64)
            pygame.draw.rect(panel, tc2, (10, cy, 130, 28), border_radius=5)
            if not td:
                pygame.draw.rect(panel, C_BORDER, (10, cy, 130, 28), 1, border_radius=5)
            ts2 = self.font_xs.render("타일디테일  " + ("ON" if td else "OFF"), True, C_TEXT)
            panel.blit(ts2, (10+65-ts2.get_width()//2, cy+7))
            self._env_btn_rects.append((pygame.Rect(PX+10, PY+cy, 130, 28), 'toggle', 'tile_detail'))
            cy += 36

        surf.blit(panel, (PX, PY))

    def _env_panel_click(self, mx, my):
        """환경 패널 버튼 클릭"""
        # 탭 / 버튼 검사
        for rect, action, val in self._env_btn_rects:
            if rect.collidepoint(mx, my):
                if action == 'tab':
                    self.env_tab = val
                elif action == 'bg_preset':
                    self.cur_bg = val
                    self._apply_bg_preset(val)
                elif action == 'terrain':
                    mat = TERRAIN_MATERIALS[val]
                    self.env['ground'] = list(mat['ground'])
                    self.env['grid']   = list(mat['grid'])
                    self.env['grid2']  = list(mat['grid2'])
                elif action == 'toggle':
                    self.env[val] = 0 if self.env[val] else 1
                return
        # 슬라이더 클릭
        for rect, key, comp, vmin, vmax, is_int in self._env_slider_rects:
            if rect.collidepoint(mx, my):
                self._env_slider_drag = (key, comp, rect.x, rect.width, vmin, vmax, is_int)
                self._env_update_slider(mx)
                return

    def _env_update_slider(self, mx):
        if not self._env_slider_drag: return
        key, comp, rx, rw, vmin, vmax, is_int = self._env_slider_drag
        norm = max(0.0, min(1.0, (mx - rx) / rw))
        val  = vmin + norm * (vmax - vmin)
        if is_int:
            val = int(round(val))
            if key == 'cloud_count' and val != len(self._clouds):
                self._clouds = []
        if comp is None:
            self.env[key] = val
        else:
            self.env[key][comp] = val
        # 별 개수 변경 시 캐시 무효화
        if key == 'stars':
            self._stars = []

    # ── DAW 타임라인 패널 전체 ────────────────────────────────────────────────
    def _draw_daw(self, surf):
        C_BG     = (20, 20, 20, 248)
        C_PANEL  = (28, 28, 28, 255)
        C_BORDER = (55, 55, 55)
        C_BLUE   = (0, 149, 232)
        C_TEXT   = (210, 210, 210)
        C_DIM    = (110, 110, 110)

        ty0 = H - TL_H

        # ── 전체 배경 ─────────────────────────────────────────────────────────
        bg = pygame.Surface((W, TL_H), pygame.SRCALPHA)
        bg.fill(C_BG)
        surf.blit(bg, (0, ty0))
        pygame.draw.line(surf, C_BORDER, (0, ty0), (W, ty0), 1)
        # picker / track 구분선
        pygame.draw.line(surf, C_BORDER, (TL_PICK_W, ty0), (TL_PICK_W, H), 1)

        # ── Transport 행 ──────────────────────────────────────────────────────
        tr_y = ty0
        # 왼쪽 제목
        title = self.font_xs.render("FIREWORK SEQUENCER", True, C_DIM)
        surf.blit(title, (8, tr_y + 10))

        # ── Transport 버튼 (클릭 영역 등록) ─────────────────────────────────
        bx = TL_PICK_W + 12
        play_lbl = "▶  Play" if not self.seq_active else "■  Stop"
        play_col = (0,100,180) if not self.seq_active else (160,40,40)
        pygame.draw.rect(surf, play_col,  (bx, tr_y+5, 80, 26), border_radius=4)
        pygame.draw.rect(surf, (90,90,90),(bx, tr_y+5, 80, 26), 1, border_radius=4)
        pl = self.font_sm.render(play_lbl, True, (230,230,230))
        surf.blit(pl, (bx+40-pl.get_width()//2, tr_y+9))
        self._play_rect = pygame.Rect(bx, tr_y+5, 80, 26)

        pygame.draw.rect(surf, (50,50,50),  (bx+90, tr_y+5, 80, 26), border_radius=4)
        pygame.draw.rect(surf, (90,90,90),  (bx+90, tr_y+5, 80, 26), 1, border_radius=4)
        rl = self.font_sm.render("↺  Reset", True, (180,180,180))
        surf.blit(rl, (bx+130-rl.get_width()//2, tr_y+9))
        self._reset_rect = pygame.Rect(bx+90, tr_y+5, 80, 26)

        zs = self.font_xs.render(f"Zoom  {self.tl_zoom:.0f}px/s   (scroll over timeline)", True, C_DIM)
        surf.blit(zs, (bx+184, tr_y+11))
        cs = self.font_xs.render(f"Clips: {len(self.placed_fw)}", True, C_DIM)
        surf.blit(cs, (W-cs.get_width()-12, tr_y+11))

        # ── Picker 영역 ───────────────────────────────────────────────────────
        pk_y = ty0 + TL_TRANSPORT
        self._picker_rects = []   # 매 프레임 초기화

        def reg(rect, action, val=None):
            """버튼 등록 헬퍼"""
            self._picker_rects.append((pygame.Rect(rect), action, val))

        def shape_btn(i, bx2, by2, bw2, bh2, active):
            bg2 = C_BLUE if active else (45,45,45)
            pygame.draw.rect(surf, bg2,      (bx2,by2,bw2,bh2), border_radius=4)
            pygame.draw.rect(surf,(70,70,70),(bx2,by2,bw2,bh2), 1, border_radius=4)
            ns = self.font_xs.render(SHAPE_NAMES[i], True, (255,255,255) if active else C_DIM)
            surf.blit(ns, (bx2+bw2//2-ns.get_width()//2, by2+bh2//2-ns.get_height()//2))
            reg((bx2,by2,bw2,bh2), 'shape', i)

        def color_swatch(i, sx2, sy2, sw2, active):
            pal = PALETTES[i]
            seg = sw2 // 3
            for j, col in enumerate(pal):
                r2,g2,b2 = (int(c*255) for c in col)
                x_off = sx2 + j * seg
                w_seg = seg if j < 2 else sw2 - 2 * seg
                pygame.draw.rect(surf, (r2,g2,b2), (x_off, sy2, w_seg, sw2))
            if active:
                pygame.draw.rect(surf, (255,255,255), (sx2-2,sy2-2,sw2+4,sw2+4), 3, border_radius=5)
            else:
                pygame.draw.rect(surf, (60,60,60), (sx2,sy2,sw2,sw2), 1, border_radius=4)
            reg((sx2,sy2,sw2,sw2), 'pal', i)

        def stepper(label, val_str, x, y, w, dec_action, inc_action):
            """[label]  [−] val [+] 컨트롤"""
            ls = self.font_xs.render(label, True, C_DIM)
            surf.blit(ls, (x, y))
            bw2 = 22
            # [−]
            dx2 = x + w - bw2*2 - 26
            pygame.draw.rect(surf,(50,50,50),(dx2,y-2,bw2,20),border_radius=3)
            pygame.draw.rect(surf,(80,80,80),(dx2,y-2,bw2,20),1,border_radius=3)
            ms = self.font_sm.render("−", True, (200,200,200))
            surf.blit(ms,(dx2+bw2//2-ms.get_width()//2, y))
            reg((dx2,y-2,bw2,20), dec_action)
            # value
            vs2 = self.font_sm.render(val_str, True, C_BLUE)
            surf.blit(vs2, (dx2+bw2+4, y-1))
            # [+]
            px2 = dx2 + bw2 + 4 + vs2.get_width() + 4
            pygame.draw.rect(surf,(50,50,50),(px2,y-2,bw2,20),border_radius=3)
            pygame.draw.rect(surf,(80,80,80),(px2,y-2,bw2,20),1,border_radius=3)
            ps = self.font_sm.render("+", True, (200,200,200))
            surf.blit(ps,(px2+bw2//2-ps.get_width()//2, y))
            reg((px2,y-2,bw2,20), inc_action)

        def delete_btn(x, y, w):
            pygame.draw.rect(surf,(100,30,30),(x,y,w,24),border_radius=4)
            pygame.draw.rect(surf,(160,60,60),(x,y,w,24),1,border_radius=4)
            ds = self.font_sm.render("Delete", True,(220,100,100))
            surf.blit(ds,(x+w//2-ds.get_width()//2, y+5))
            reg((x,y,w,24),'delete')

        PW = TL_PICK_W - 10   # 유효 너비
        BH, BW = 22, (PW-14)//2   # 버튼 높이, 너비 (2열)

        if self.mode == MODE_FW:
            COLS3 = 3
            BW3 = (PW - (COLS3-1)*4) // COLS3
            if isinstance(self.selected, PlacedFirework):
                # 선택된 폭죽 개별 편집
                fw = self.selected
                sel_label = self.font_xs.render("● 선택된 폭죽", True, C_BLUE)
                surf.blit(sel_label, (8, pk_y+2))
                surf.blit(self.font_xs.render("SHAPE", True, C_DIM),(8, pk_y+18))
                for i in range(len(SHAPE_NAMES)):
                    ci,ri = i%COLS3, i//COLS3
                    shape_btn(i, 8+ci*(BW3+4), pk_y+32+ri*(BH+4), BW3, BH-2, i==fw.shape_idx)
                n_rows3 = (len(SHAPE_NAMES) + COLS3 - 1) // COLS3
                gy = pk_y+32+n_rows3*(BH+4)+6
                surf.blit(self.font_xs.render("COLOR", True, C_DIM),(8, gy))
                sw=32
                for i in range(len(PALETTES)):
                    color_swatch(i, 8+i*(sw+3), gy+13, sw, i==fw.pal_idx)
                dy2 = gy+13+sw+8
                stepper("DELAY", f"{fw.delay:.1f}s", 8, dy2, PW, 'delay_dec','delay_inc')
                delete_btn(8, dy2+30, PW-6)
            else:
                # ── 상단 탭: [단발] / [케이크] ────────────────────────────
                TW = (PW - 4) // 2
                for ti, tlbl in enumerate(['단발', '케이크']):
                    tx = 8 + ti*(TW+4)
                    act_t = (ti == (1 if self.cake_mode else 0))
                    pygame.draw.rect(surf, C_BLUE if act_t else (40,40,40), (tx,pk_y+4,TW,22), border_radius=4)
                    pygame.draw.rect(surf,(70,70,70),(tx,pk_y+4,TW,22),1,border_radius=4)
                    ts2 = self.font_xs.render(tlbl, True,(255,255,255) if act_t else C_DIM)
                    surf.blit(ts2,(tx+TW//2-ts2.get_width()//2, pk_y+8))
                    reg((tx,pk_y+4,TW,22),'cake_toggle',ti)
                cy = pk_y + 32

                if not self.cake_mode:
                    # ── 단발 탭 ───────────────────────────────────────────
                    surf.blit(self.font_xs.render("SHAPE", True, C_DIM),(8, cy))
                    cy += 14
                    for i in range(len(SHAPE_NAMES)):
                        ci,ri = i%COLS3, i//COLS3
                        shape_btn(i, 8+ci*(BW3+4), cy+ri*(BH+4), BW3, BH, i==self.cur_shape)
                    n_rows3 = (len(SHAPE_NAMES)+COLS3-1)//COLS3
                    cy += n_rows3*(BH+4)+8
                    surf.blit(self.font_xs.render("COLOR", True, C_DIM),(8, cy))
                    sw=32
                    for i in range(len(PALETTES)):
                        color_swatch(i, 8+i*(sw+3), cy+14, sw, i==self.cur_pal)
                    cy += 14+sw+10
                    # 발사 각도
                    stepper("발사각도", f"{self.cur_launch_angle:.0f}deg", 8, cy, PW, 'lang_dec','lang_inc')
                    cy += 24
                    stepper("발사방향", f"{self.cur_launch_dir:.0f}deg", 8, cy, PW, 'ldir_dec','ldir_inc')
                    cy += 24
                    stepper("DELAY", f"{self.cur_delay:.1f}s", 8, cy, PW, 'delay_dec','delay_inc')

                else:
                    # ── 케이크 탭 (2열 압축 레이아웃 — 20px/행) ──────────────
                    HW = PW//2 - 3   # 반쪽 너비

                    def stp2(l1,v1,d1,i1, l2,v2,d2,i2, y):
                        """두 stepper 를 좌우로 배치"""
                        stepper(l1,v1, 8,        y, HW, d1,i1)
                        stepper(l2,v2, 8+HW+4,   y, HW, d2,i2)

                    def row_btns(items, action, cur, y, h=20):
                        bw3=(PW-4*(len(items)-1))//len(items)
                        for ii,(lbl,val) in enumerate(items):
                            bx3=8+ii*(bw3+4); act3=(cur==val)
                            pygame.draw.rect(surf,C_BLUE if act3 else (45,45,45),(bx3,y,bw3,h),border_radius=3)
                            pygame.draw.rect(surf,(70,70,70),(bx3,y,bw3,h),1,border_radius=3)
                            ts3=self.font_xs.render(lbl,True,(255,255,255) if act3 else C_DIM)
                            surf.blit(ts3,(bx3+bw3//2-ts3.get_width()//2,y+3))
                            reg((bx3,y,bw3,h),action,val)

                    # ① 패턴 선택
                    row_btns([('네모',0),('부채꼴',1)], 'cake_pattern', self.cake_pattern, cy); cy+=22

                    # ② 패턴별 파라미터 (2열, 20px/행)
                    if self.cake_pattern == 0:
                        stp2("가로",f"{self.cake_cols}",'cake_cols_dec','cake_cols_inc',
                             "세로",f"{self.cake_rows}",'cake_rows_dec','cake_rows_inc', cy); cy+=22
                        stp2("간격",f"{self.cake_spacing:.0f}u",'cake_sp_dec','cake_sp_inc',
                             "방향",f"{self.cake_dir_ang:.0f}d",'cake_da_dec','cake_da_inc', cy); cy+=22
                    else:
                        stp2("발수", f"{self.cake_fan_n}발",'cake_fn_dec','cake_fn_inc',
                             "각도", f"{self.cake_fan_deg:.0f}d",'cake_fd_dec','cake_fd_inc', cy); cy+=22
                        stp2("방향", f"{self.cake_fan_dir:.0f}d",'cake_fdir_dec','cake_fdir_inc',
                             "기울기",f"{self.cake_fan_tilt:.0f}d",'cake_ft_dec','cake_ft_inc', cy); cy+=22

                    # ③ 발사 속도
                    row_btns([(n,i) for i,n in enumerate(CAKE_SPD_NAMES)],
                             'cake_spd', self.cake_spd, cy); cy+=22

                    # ④ COLOR
                    surf.blit(self.font_xs.render("COLOR", True, C_DIM),(8, cy))
                    sw=28
                    for i in range(len(PALETTES)):
                        color_swatch(i, 8+i*(sw+2), cy+13, sw, i==self.cur_pal)
                    cy += 13+sw+8

                    # ⑤ 시작 딜레이
                    stepper("시작딜레이", f"{self.cur_delay:.1f}s", 8, cy, PW, 'delay_dec','delay_inc')

        elif self.mode == MODE_ST:
            surf.blit(self.font_xs.render("STRUCTURE TYPE", True, C_DIM),(8, pk_y+6))
            for i in range(len(ST_NAMES)):
                ci,ri = i%2, i//2
                active = (i==self.cur_st)
                bg2 = C_BLUE if active else (45,45,45)
                pygame.draw.rect(surf,bg2,(8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),border_radius=4)
                pygame.draw.rect(surf,(70,70,70),(8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),1,border_radius=4)
                ns=self.font_xs.render(ST_NAMES[i],True,(255,255,255) if active else C_DIM)
                surf.blit(ns,(8+ci*(BW+6)+BW//2-ns.get_width()//2, pk_y+20+ri*(BH+4)+BH//2-ns.get_height()//2))
                reg((8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),'st_type',i)
            gy2 = pk_y+20+3*(BH+4)+10
            stepper("SCALE", f"{self.cur_scale:.1f}x", 8, gy2, PW, 'scale_dec','scale_inc')

        elif self.mode == MODE_SEL:
            if isinstance(self.selected, PlacedFirework):
                fw = self.selected
                COLS3 = 3
                BW3 = (PW - (COLS3-1)*4) // COLS3
                surf.blit(self.font_xs.render("SHAPE", True, C_DIM),(8, pk_y+4))
                for i in range(len(SHAPE_NAMES)):
                    ci,ri = i%COLS3, i//COLS3
                    shape_btn(i, 8+ci*(BW3+4), pk_y+18+ri*(BH+4), BW3, BH-2, i==fw.shape_idx)
                n_rows3 = (len(SHAPE_NAMES) + COLS3 - 1) // COLS3
                gy = pk_y+18+n_rows3*(BH+4)+6
                surf.blit(self.font_xs.render("COLOR", True, C_DIM),(8, gy))
                sw=32
                for i in range(len(PALETTES)):
                    color_swatch(i, 8+i*(sw+3), gy+13, sw, i==fw.pal_idx)
                dy2=gy+13+sw+8
                stepper("DELAY", f"{fw.delay:.1f}s", 8, dy2, PW, 'delay_dec','delay_inc')
                delete_btn(8, dy2+30, PW-6)

            elif isinstance(self.selected, Structure):
                st = self.selected
                surf.blit(self.font_xs.render("STRUCTURE TYPE", True, C_DIM),(8, pk_y+6))
                for i in range(len(ST_NAMES)):
                    ci,ri = i%2, i//2
                    active = (i==st.type_idx)
                    bg2 = C_BLUE if active else (45,45,45)
                    pygame.draw.rect(surf,bg2,(8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),border_radius=4)
                    pygame.draw.rect(surf,(70,70,70),(8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),1,border_radius=4)
                    ns=self.font_xs.render(ST_NAMES[i],True,(255,255,255) if active else C_DIM)
                    surf.blit(ns,(8+ci*(BW+6)+BW//2-ns.get_width()//2, pk_y+20+ri*(BH+4)+BH//2-ns.get_height()//2))
                    reg((8+ci*(BW+6),pk_y+20+ri*(BH+4),BW,BH),'st_type',i)
                gy2=pk_y+20+3*(BH+4)+8
                stepper("SCALE", f"{st.scale:.1f}x", 8, gy2, PW, 'scale_dec','scale_inc')
                delete_btn(8, gy2+30, PW-6)
            else:
                hint = self.font_sm.render("Click an object to select", True, C_DIM)
                surf.blit(hint, (TL_PICK_W//2-hint.get_width()//2, pk_y+60))

        else:  # CAM
            for i,(k,v) in enumerate([("Launchers",str(len(self.placed_fw))),
                                       ("Structures",str(len(self.placed_st))),
                                       ("Particles",str(len(self.particles)))]):
                surf.blit(self.font_xs.render(k,True,C_DIM),(10,pk_y+12+i*32))
                surf.blit(self.font_sm.render(v,True,C_TEXT),(10,pk_y+24+i*32))

        # ── 눈금자 ────────────────────────────────────────────────────────────
        ruler_y = ty0 + TL_TRANSPORT
        pygame.draw.rect(surf, (24,24,24), (TL_PICK_W, ruler_y, W-TL_PICK_W, TL_RULER_H))
        pygame.draw.line(surf, C_BORDER, (TL_PICK_W, ruler_y+TL_RULER_H-1),
                         (W, ruler_y+TL_RULER_H-1), 1)

        # 눈금 간격: zoom에 따라 자동 조정
        interval = 1.0
        if self.tl_zoom > 150: interval = 0.5
        if self.tl_zoom > 300: interval = 0.25
        if self.tl_zoom < 40:  interval = 2.0

        t = math.ceil(self.tl_offset / interval) * interval
        while True:
            rx = self._tl_x(t)
            if rx > W: break
            if rx >= TL_PICK_W:
                is_major = abs(round(t) - t) < 0.01
                tick_h = 10 if is_major else 5
                pygame.draw.line(surf, (90,90,90) if is_major else (55,55,55),
                                 (rx, ruler_y+TL_RULER_H-tick_h),
                                 (rx, ruler_y+TL_RULER_H-1), 1)
                if is_major:
                    ts = self.font_xs.render(f"{t:.0f}s", True, (100,100,100))
                    surf.blit(ts, (rx - ts.get_width()//2, ruler_y + 2))
            t += interval

        # ── 클립 트랙 ─────────────────────────────────────────────────────────
        track_y = ty0 + TL_TRANSPORT + TL_RULER_H
        track_h = H - track_y

        # 트랙 배경 줄무늬
        for i in range(0, W - TL_PICK_W, 40):
            rx = TL_PICK_W + i
            pygame.draw.line(surf, (26,26,26), (rx, track_y), (rx, H), 1)

        # 클립 블록
        for fw in self.placed_fw:
            cx2 = self._tl_x(fw.delay)
            if cx2 < TL_PICK_W or cx2 > W + CLIP_W: continue

            r,g,b = (int(c*255) for c in PALETTES[fw.pal_idx][0])
            is_sel = (self.selected is fw)
            is_fired = fw.fired

            clip_x = cx2 - CLIP_W//2
            clip_y = track_y + 6
            clip_h = track_h - 14

            # 클립 본체
            alpha = 200 if not is_fired else 100
            clip_surf = pygame.Surface((CLIP_W, clip_h), pygame.SRCALPHA)
            clip_surf.fill((r//3, g//3, b//3, alpha))
            surf.blit(clip_surf, (clip_x, clip_y))

            # 왼쪽 색상 바
            pygame.draw.rect(surf, (r,g,b), (clip_x, clip_y, 4, clip_h), border_radius=2)

            # 테두리
            border_col = C_BLUE if is_sel else (r,g,b)
            border_w = 2 if is_sel else 1
            pygame.draw.rect(surf, border_col, (clip_x, clip_y, CLIP_W, clip_h),
                             border_w, border_radius=3)

            # 클립 텍스트
            sn = self.font_xs.render(SHAPE_NAMES[fw.shape_idx], True,
                                     (200,200,200) if not is_fired else (100,100,100))
            ds = self.font_xs.render(f"{fw.delay:.1f}s", True,
                                     (r,g,b) if not is_fired else (80,80,80))
            surf.blit(sn, (clip_x + 7, clip_y + 5))
            surf.blit(ds, (clip_x + 7, clip_y + clip_h - ds.get_height() - 5))

            # 드래그 중 핸들
            if is_sel:
                pygame.draw.circle(surf, C_BLUE, (cx2, track_y + track_h//2), 5)

        # ── 플레이헤드 ────────────────────────────────────────────────────────
        if self.seq_active:
            elapsed = time.time() - self.seq_start
            phx = self._tl_x(elapsed)
            if TL_PICK_W <= phx <= W:
                pygame.draw.line(surf, C_BLUE, (phx, ruler_y), (phx, H), 2)
                # 헤드 삼각형
                pygame.draw.polygon(surf, C_BLUE,
                    [(phx-6, ruler_y), (phx+6, ruler_y), (phx, ruler_y+10)])

    def _draw_timeline(self, surf):
        if not self.placed_fw: return
        bh = 80   # 하단 바 높이
        tw, th = W - 80, 18
        tx, ty = 40, H - bh - th - 28

        # 배경
        bg = pygame.Surface((tw+4, th+22), pygame.SRCALPHA)
        bg.fill((25,25,25,220))
        surf.blit(bg, (tx-4, ty-4))
        pygame.draw.rect(surf,(55,55,55),(tx,ty,tw,th),1)

        # 레이블
        tl = self.font_xs.render("TIMELINE", True, (100,100,100))
        surf.blit(tl, (tx, ty-16))

        max_d = max(fw.delay for fw in self.placed_fw)
        if max_d < 0.1: max_d = 1.0

        for fw in self.placed_fw:
            ratio = fw.delay/max_d
            px = tx + int(ratio*(tw-8)) + 4
            pc = tuple(int(c*255) for c in PALETTES[fw.pal_idx][0])
            col = (255,255,80) if fw.fired else pc
            r = 7 if (self.selected is fw) else 5
            pygame.draw.circle(surf, col, (px, ty+th//2), r)
            if self.selected is fw:
                pygame.draw.circle(surf, (0,149,232), (px, ty+th//2), r+2, 2)

        for i in range(7):
            t2 = max_d*(i/6)
            px = tx + int((i/6)*(tw-8)) + 4
            pygame.draw.line(surf,(60,60,60),(px,ty),(px,ty+5),1)
            s = self.font_xs.render(f"{t2:.1f}s", True, (100,100,100))
            surf.blit(s, (px-12, ty+th+3))

        if self.seq_active:
            elapsed = time.time()-self.seq_start
            ratio = min(elapsed/max_d, 1.0)
            px = tx + int(ratio*(tw-8)) + 4
            pygame.draw.line(surf,(0,149,232),(px,ty-2),(px,ty+th+2),2)

    def _draw_bottombar(self, surf):
        # ── Studio 하단 Properties 바 ─────────────────────────────────
        bh = 80
        bg = pygame.Surface((W, bh), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 245))
        surf.blit(bg, (0, H-bh))
        pygame.draw.line(surf, (60,60,60), (0, H-bh), (W, H-bh), 1)

        BLUE = (0,149,232); WHITE = (220,220,220); DIM = (140,140,140); KEY_COL = (100,100,100)

        def prop(surf, x, y, label, value, key=""):
            ls = self.font_xs.render(label, True, DIM)
            surf.blit(ls, (x, y))
            vs = self.font_sm.render(value, True, WHITE)
            surf.blit(vs, (x, y+14))
            if key:
                ks = self.font_xs.render(key, True, KEY_COL)
                surf.blit(ks, (x, y+31))
            return x + max(ls.get_width(), vs.get_width()) + 22

        # 왼쪽: 모드 표시판
        mode_labels = ["CAMERA","FIREWORK","MODEL","SELECT"]
        ml = self.font_lg.render(mode_labels[self.mode], True, BLUE)
        surf.blit(ml, (16, H-bh+18))
        pygame.draw.line(surf, (55,55,55), (16+ml.get_width()+16, H-bh+8),
                         (16+ml.get_width()+16, H-10), 1)

        cx = 16 + ml.get_width() + 30

        if self.mode == MODE_FW:
            cx = prop(surf, cx, H-bh+8, "Shape",   SHAPE_NAMES[self.cur_shape], "T")
            cx = prop(surf, cx, H-bh+8, "Color",   PAL_NAMES[self.cur_pal],     "P")
            cx = prop(surf, cx, H-bh+8, "Delay",   f"{self.cur_delay:.1f}s",    "← →")
            prop(surf, cx, H-bh+8, "Action", "LClick to Place", "")

        elif self.mode == MODE_ST:
            cx = prop(surf, cx, H-bh+8, "Type",    ST_NAMES[self.cur_st],  "↑ ↓")
            cx = prop(surf, cx, H-bh+8, "Scale",   f"{self.cur_scale:.1f}", "[ ]")
            prop(surf, cx, H-bh+8, "Action", "LClick to Place", "")

        elif self.mode == MODE_SEL:
            if isinstance(self.selected, PlacedFirework):
                fw = self.selected
                cx = prop(surf, cx, H-bh+8, "Shape", SHAPE_NAMES[fw.shape_idx], "T")
                cx = prop(surf, cx, H-bh+8, "Color", PAL_NAMES[fw.pal_idx],     "P")
                cx = prop(surf, cx, H-bh+8, "Delay", f"{fw.delay:.1f}s",        "← →")
                prop(surf, cx, H-bh+8, "Delete", "Del", "")
            elif isinstance(self.selected, Structure):
                st = self.selected
                cx = prop(surf, cx, H-bh+8, "Type",  ST_NAMES[st.type_idx], "")
                cx = prop(surf, cx, H-bh+8, "Scale", f"{st.scale:.1f}",     "[ ]")
                prop(surf, cx, H-bh+8, "Delete", "Del", "")
            else:
                prop(surf, cx, H-bh+8, "Tip", "Click an object to select", "")

        else:  # 카메라
            cx = prop(surf, cx, H-bh+8, "Launchers", f"{len(self.placed_fw)}", "")
            cx = prop(surf, cx, H-bh+8, "Structures",f"{len(self.placed_st)}", "")
            prop(surf, cx,     H-bh+8,  "Particles",  f"{len(self.particles)}", "")

        # 오른쪽: 씬 통계
        stats = [
            f"Launchers  {len(self.placed_fw)}",
            f"Structures  {len(self.placed_st)}",
            f"Particles  {len(self.particles)}",
        ]
        rx = W - 14
        for st in reversed(stats):
            ss = self.font_xs.render(st, True, (100,100,100))
            rx -= ss.get_width() + 20
            surf.blit(ss, (rx, H-bh+32))
            pygame.draw.line(surf,(55,55,55),(rx+ss.get_width()+9,H-bh+26),(rx+ss.get_width()+9,H-bh+50),1)

    def _blit_surface(self, surf):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0,W,0,H,-1,1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        data = pygame.image.tostring(surf,'RGBA',True)
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,W,H,0,GL_RGBA,GL_UNSIGNED_BYTE,data)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glEnable(GL_TEXTURE_2D)
        glColor4f(1,1,1,1)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(0,0)
        glTexCoord2f(1,0); glVertex2f(W,0)
        glTexCoord2f(1,1); glVertex2f(W,H)
        glTexCoord2f(0,1); glVertex2f(0,H)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([tid])
        glBlendFunc(GL_SRC_ALPHA,GL_ONE)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # ── 메인 루프 ─────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == '__main__':
    Game().run()
