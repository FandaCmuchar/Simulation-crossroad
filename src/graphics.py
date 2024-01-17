import tkinter as tk


class Graphics:
    """Visualize simulation."""
    def __init__(self, window, size):
        self.car_size = 0
        self.text_size = 0
        self.win = window
        self.canvas = tk.Canvas(self.win, width=1000, height=1000, bg="grey80")
        self.canvas.pack()
        self.canvas.update()
        self.size = size
        self.car_spawn_points = {}
        self.cars_queue_count_pos = {}
        self.traffic_lights = {}
        self.cr_len = 0
        self.car_queue_text = {}
        self.draw_crossroads(size)
        self.cars = {}
        self.car_labels = {}

    def display_car(self, side, fill, id, text=''):
        """Create, save and display graphical representation of the car."""
        x0, y0 = self.car_spawn_points[side]
        self.cars[id] = self.canvas.create_rectangle(x0, y0, x0 + self.car_size, y0 + self.car_size, fill=fill, tags='car'+str(id))
        self.car_labels[id] = self.canvas.create_text(x0+self.car_size/2, y0+self.car_size/2,
                                                      font=("Arial", int(0.6*self.text_size)),text=str(id)+ f' {text}', tags='car'+str(id))
        self.canvas.update()

    def change_car_queue_text(self, dir, count):
        """Changes text that represents number of waiting cars before crossroad."""
        self.canvas.itemconfig(self.car_queue_text[dir], text=str(count))
        self.canvas.update()

    def delete_car(self, id):
        """Delete graphical representation of the car (usually when in finish)"""
        self.canvas.delete('car'+str(id))
        self.canvas.update()

    def move_car(self, steps, direction, id):
        """Move graphical representation of the car."""
        speed = (1.58*self.size) / steps
        speedY = direction[0]*speed
        speedX = direction[1]*speed
        if self.cars[id] is not None:
            self.canvas.move(self.cars[id], speedX, speedY)
            self.canvas.move(self.car_labels[id], speedX, speedY)
            self.canvas.update()

    def draw_crossroads(self, size):
        """Counts ratio and draw crossroad and traffic lights."""
        step = size / 5
        cr_size = size * step
        road_len = 0.9 * cr_size
        offset = 0.75 * cr_size
        width = 0.3 * cr_size
        shift = 4 * step
        self.cr_len = 2 * road_len

        self.car_size = width / 3.9
        self.text_size = int(size / 2.5)

        self.car_spawn_points['W'] = (shift, offset + width / 2 + width / 8 + shift)
        self.car_spawn_points['E'] = (shift + 2 * road_len - self.car_size, offset + width / 8 + shift)
        self.car_spawn_points['N'] = (offset + shift + width / 8, shift)
        self.car_spawn_points['S'] = (offset + width / 2 + width / 8 + shift, shift + 2 * road_len - self.car_size)

        font = ("Arial", self.text_size)
        self.cars_queue_count_pos['N'] = (
            self.car_spawn_points['N'][0] + width / 8, self.car_spawn_points['N'][1] - 2 * step)
        self.cars_queue_count_pos['S'] = (
            self.car_spawn_points['S'][0] + width / 8, self.car_spawn_points['S'][1] + self.car_size + 2 * step)
        self.cars_queue_count_pos['W'] = (
            self.car_spawn_points['W'][0] - 2 * step, self.car_spawn_points['W'][1] + width / 8)
        self.cars_queue_count_pos['E'] = (
            self.car_spawn_points['E'][0] + self.car_size + 2 * step, self.car_spawn_points['E'][1] + width / 8)

        dirs = ['N', 'S', 'W', 'E']
        for d in dirs:
            x, y = self.cars_queue_count_pos[d]
            self.car_queue_text[d] = self.canvas.create_text(x, y, font=font, text=d)

        outline_col = "black"
        # White side way lines
        self.canvas.create_rectangle(shift, offset - step + shift, road_len * 2 + shift, offset + shift, fill="white",
                                     outline=outline_col)
        self.canvas.create_rectangle(shift, offset + width + shift, road_len * 2 + shift, offset + width + step + shift,
                                     fill="white", outline=outline_col)

        self.canvas.create_rectangle(offset - step + shift, shift, offset + shift, road_len * 2 + shift, fill="white",
                                     outline=outline_col)
        self.canvas.create_rectangle(offset + width + shift, shift, offset + width + step + shift, road_len * 2 + shift,
                                     fill="white", outline=outline_col)

        # Road
        self.canvas.create_rectangle(shift, offset + shift, road_len * 2 + shift, offset + width + shift, fill="black")
        self.canvas.create_rectangle(offset + shift, shift, offset + width + shift, road_len * 2 + shift, fill="black")

        # White middle lines
        self.canvas.create_rectangle(shift, offset + width / 2 - step / 4 + shift, offset - step + shift,
                                     offset + width / 2 + step / 4 + shift,
                                     fill="white", outline=outline_col)
        self.canvas.create_rectangle(offset + width + step + shift, offset + width / 2 - step / 4 + shift,
                                     2 * road_len + shift,
                                     offset + width / 2 + step / 4 + shift, fill="white", outline=outline_col)

        self.canvas.create_rectangle(offset + width / 2 - step / 4 + shift, shift,
                                     offset + width / 2 + step / 4 + shift, offset - step + shift,
                                     fill="white", outline=outline_col)
        self.canvas.create_rectangle(offset + width / 2 - step / 4 + shift, offset + width + step + shift,
                                     offset + width / 2 + step / 4 + shift,
                                     road_len * 2 + shift, fill="white", outline=outline_col)

        # White line before crossroads
        # =
        self.canvas.create_rectangle(offset + width / 2 - step / 4 + shift, offset + width + step + shift,
                                     offset + width + shift,
                                     offset + width + 2 * step + shift, fill="white", outline=outline_col)
        self.canvas.create_rectangle(offset + shift, offset - step + shift, offset + width / 2 + step / 4 + shift,
                                     offset - 2 * step + shift, fill="white", outline=outline_col)

        # ||
        self.canvas.create_rectangle(offset - step + shift, offset + width / 2 - step / 4 + shift,
                                     offset - 2 * step + shift,
                                     offset + width + shift, fill="white", outline=outline_col)
        self.canvas.create_rectangle(offset + step + width + shift, offset + shift, offset + 2 * step + width + shift,
                                     offset + width / 2 + step / 4 + shift, fill="white", outline=outline_col)

        self.traffic_lights['N'] = TrafficLights(road_len + shift - width / 2 - 4 * step,
                                                 road_len - width + shift - step / 3, size,
                                                 self.canvas, green_down=False)
        self.traffic_lights['S'] = TrafficLights(road_len + width / 2 + shift + 2 * step,
                                                 road_len + width / 2 + 2 * step + shift, size,
                                                 self.canvas)
        self.traffic_lights['W'] = TrafficLights(road_len + shift - width - step / 3,
                                                 road_len + 2 * step + width / 2 + shift, size,
                                                 self.canvas, vertical=False, green_down=False)
        self.traffic_lights['E'] = TrafficLights(road_len + 2 * step + width / 2 + shift,
                                                 road_len + shift - width / 2 - 4 * step, size, self.canvas,
                                                 vertical=False)

        for t in self.traffic_lights.values():
            t.light('r')
        self.canvas.update()


class TrafficLights:
    cols = {'r': "red", 'o': "orange", 'g': "green"}

    def __init__(self, x0, y0, size, canvas, vertical=True, green_down=True):
        self.x = x0
        self.y = y0
        self.canvas = canvas
        self.wide = 0.4 * size
        self.len = 3 * self.wide
        self.light_size = 0.9 * self.wide
        self.step = 0.05 * self.len
        self.vertical = vertical
        self.green_down = green_down
        self.curr_col = 'g'
        self.lights = []
        self.light_pos = self.draw()

    def draw(self):
        """Initially count and draw traffic lights graphical representation."""
        if self.vertical:
            light_pos = [(self.x + self.step / 3, self.y + self.step / 2),
                              (self.x + self.step / 3, self.y + self.step + self.light_size),
                              (self.x + self.step / 3, self.y + 1.5 * self.step + 2 * self.light_size)]
            self.canvas.create_rectangle(self.x, self.y, self.x + self.wide, self.y + self.len, fill="black")
        else:
            light_pos = [(self.x + self.step / 2,self.y + self.step / 3),
                              (self.x + self.step + self.light_size, self.y + self.step / 3),
                              (self.x + 1.5 * self.step + 2 * self.light_size, self.y + self.step / 3)]
            self.canvas.create_rectangle(self.x, self.y, self.x + self.len, self.y + self.wide, fill="black")
        for x, y in light_pos:
            if self.vertical:
                self.lights.append(self.canvas.create_oval(x, y, x + self.light_size, y + self.light_size, fill="grey"))
            else:
                self.lights.append(self.canvas.create_oval(x, y, x + self.light_size, y + self.light_size, fill="grey"))
        self.canvas.update()
        return light_pos

    def light(self, col='r'):
        """Light given color on traffic light."""
        if self.curr_col == col:
            return

        if self.green_down:
            col_idx = {'r': 0, 'o': 1, 'g': 2}
        else:
            col_idx = {'r': 2, 'o': 1, 'g': 0}

        if col == 'ro':
            self.canvas.itemconfig(self.lights[1], fill=self.cols['o'])
            col = col[1]
        else:
            idx = col_idx[col]
            if col == 'g':
                self.canvas.itemconfig(self.lights[idx], fill=self.cols['g'])
                self.canvas.itemconfig(self.lights[col_idx['r']], fill='grey')
                self.canvas.itemconfig(self.lights[col_idx['o']], fill='grey')
            elif col == 'o':
                self.canvas.itemconfig(self.lights[idx], fill=self.cols['o'])
                self.canvas.itemconfig(self.lights[col_idx['g']], fill='grey')
            else:
                self.canvas.itemconfig(self.lights[idx], fill=self.cols['r'])
                self.canvas.itemconfig(self.lights[col_idx['o']], fill='grey')

        self.curr_col = col
