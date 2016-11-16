import math
from collections import OrderedDict

from Field.FieldHandler import drawing_offset, cell_size, step_size, Selectable, d_m
from Field.functions import dist, set_l


class Sensor(Selectable):
    def __init__(self, wall, pos=cell_size//2, alpha=0):
        super(Sensor, self).__init__(color="#ff3300", selected_color="#00ffff")
        self._pos = pos  # middle of the wall
        self._alpha = alpha  # 0 means perpendicular to the wall, it is in radians
        self._alpha_max = 0.786
        self._wall = wall
        self._draw_radius = 3 * d_m
        self._select_radius = 6
        self._effect_radius = 40 * step_size  # in step_size
        self._effect_arc = 0.5  # cos(60) = 0.5

        self._number_of_pixels = 0
        self._max_number_of_pixels = 1676

    @property
    def wall(self):
        return self._wall

    @property
    def pos(self):
        return self._pos

    @property
    def alpha(self):
        return self._alpha

    @property
    def number_of_pixels(self):
        return self._number_of_pixels

    @number_of_pixels.setter
    def number_of_pixels(self, value):
        self._number_of_pixels = value

    @property
    def max_number_of_pixels(self):
        return self._max_number_of_pixels

    @property
    def room_id(self):
        return self._wall.room_id

    @property
    def effect_radius(self):
        return self._effect_radius

    @property
    def effect_arc(self):
        return self._effect_arc

    def move(self, m):
        self._pos += m
        # TODO add alpha handling - now its a sudden change
        if self._pos < 1:
            self._wall = self._wall.e2r
            self._pos += cell_size-2

        if self._pos > cell_size-2:
            self._wall = self._wall.e2l
            self._pos -= cell_size-2

    def rotate(self, a):
        self._alpha += a
        if math.fabs(self._alpha) > self._alpha_max:
            self._alpha = self._alpha_max if self._alpha > 0 else -self._alpha_max

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
        pos = [p * d_m + drawing_offset for p in self.get_pos()]
        v = set_l(self.get_look_dir(), 15 * d_m)
        canvas.create_line(pos[0], pos[1], pos[0] + v[0], pos[1] + v[1], fill=self.color, width=self.width)
        canvas.create_oval(pos[0] - self._draw_radius, pos[1] - self._draw_radius,
                           pos[0] + self._draw_radius, pos[1] + self._draw_radius, fill=self.color)

    def point_is_inside(self, m_x, m_y):
        pos = self.get_pos()
        return dist(pos, [m_x, m_y]) < self._select_radius


class SensorField:
    def __init__(self, field, field_id, parents_ids=('', '')):
        self._field_id = field_id
        self._parents_ids = parents_ids
        self._field = field
        self._batches = OrderedDict()
        self._cost = 0
        for room in field.rooms.values():
            self._batches[room.id] = SensorBatch(room)

    @property
    def field_id(self):
        return self._field_id

    @property
    def parents_ids(self):
        return self._parents_ids

    @property
    def cost(self):
        return self._cost

    @property
    def batches(self):
        return self._batches

    def create_new_batch(self, room):
        self._batches[room.id] = SensorBatch(room)

    def check_room_sensors_visibility(self):
        for batch in self._batches.values():
            batch.check_sensors_visibility()

    def calculate_cost(self):
        self._cost = 0
        for batch in self._batches.values():
            self._cost += batch.calculate_cost()
        print(self._cost)
        return self._cost

    def remove_batch(self, room_id):
        self._batches.pop(room_id, None)

    def delete_sensors(self, sensors):
        for sensor in sensors:
            room = self._batches[sensor.room_id]
            room.remove_sensor(sensor)

    def delete_all(self):
        for room in self._batches.values():
            room.delete_all()


class SensorBatch:
    def __init__(self, room):
        self._id = room.id
        self._room = room
        self._sensors = []
        self._cost = 0

    def remove_sensors(self):
        self._sensors = []

    def remove_sensor(self, sensor):
        if isinstance(sensor, int):
            sensor = self._sensors[sensor]
        else:
            if sensor not in self._sensors:
                return
        self._sensors.remove(sensor)

    @property
    def cost(self):
        return self._cost

    @property
    def id(self):
        return self._id

    @property
    def room(self):
        return self._room

    @property
    def sensors(self):
        return self._sensors

    def create_sensor_on(self, wall, pos=cell_size//2, alpha=0):
        if isinstance(wall, int):
            wall = self.room.walls[wall]
        sensor = Sensor(wall, pos, alpha)
        self._sensors += [sensor]

    def check_sensors_visibility(self):
        for sensor in self._sensors:
            sensor.number_of_pixels = 0
        for cell in self._room.cells:
            for pixel in cell.pixels:
                pixel.number_of_sensors = 0
                for sensor in self._sensors:
                    pixel.check_sensor_visibility(self, sensor)

    def calculate_cost(self):
        self._cost = 0
        for cell in self._room.cells:
            for pixel in cell.pixels:
                if pixel.number_of_sensors == 0:
                    self._cost += 3
                if pixel.number_of_sensors > 1:
                    self._cost += pixel.number_of_sensors - 1
        for sensor in self._sensors:
            self._cost += (sensor.max_number_of_pixels - sensor.number_of_pixels) * 2
        # self._cost += room_cost / len(room.sensors)
        return self._cost
