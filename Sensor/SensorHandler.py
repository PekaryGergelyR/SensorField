import math

from Field.FieldHandler import drawing_offset, cell_size, step_size, Selectable


class Sensor(Selectable):
    def __init__(self, wall, pos=cell_size//2, alpha=0):
        super(Sensor, self).__init__(color="#ff3300", selected_color="#ff55ff")
        self._pos = pos  # middle of the wall
        self._alpha = alpha  # 0 means perpendicular to the wall, it is in radians
        self._wall = wall
        self._draw_radius = 3
        self._select_radius = 6
        self._effect_radius = 40  # in step_size
        self._effect_arc = 0.5  # cos(60)

    @property
    def room_id(self):
        return self._wall.room_id

    @property
    def effect_radius(self):
        return self._effect_radius

    @property
    def effect_arc(self):
        return self._effect_arc

    def get_look_dir(self):
        wall_normal = [[0, 1], [-1, 0], [0, -1], [1, 0]]
        v = wall_normal[self._wall.orientation]
        return [math.cos(self._alpha)*v[0]+math.sin(self._alpha)*v[1],
                -math.sin(self._alpha)*v[0]+math.cos(self._alpha)*v[1]]

    def get_pos(self):
        # Right corner if looking inward
        x1 = self._wall.corners[0].pos[1] * cell_size
        y1 = self._wall.corners[0].pos[0] * cell_size

        sensor_pos_rel2wall = [[step_size, 0], [0, -step_size], [-step_size, 0], [0, step_size]]
        sensor_pos_on_wall = [[0, self._pos], [self._pos, 0], [0, -self._pos], [-self._pos, 0]]
        x = x1 + sensor_pos_on_wall[self._wall.orientation][1]+sensor_pos_rel2wall[self._wall.orientation][1]
        y = y1 + sensor_pos_on_wall[self._wall.orientation][0] + sensor_pos_rel2wall[self._wall.orientation][0]
        return [x, y]

    def draw(self, canvas):
        pos = [p + drawing_offset for p in self.get_pos()]
        canvas.create_oval(pos[0] - self._draw_radius, pos[1] - self._draw_radius,
                           pos[0] + self._draw_radius, pos[1] + self._draw_radius, fill=self.color)

    @staticmethod
    def _sqr(v):
        return v*v

    def _dist(self, p1, p2):
        return self._sqr(p1[0] - p2[0]) + self._sqr(p1[1] - p2[1])

    def point_is_inside(self, m_x, m_y):
        pos = [p + drawing_offset for p in self.get_pos()]
        return self._dist(pos, [m_x, m_y]) < self._sqr(self._draw_radius * 2)
