"""
Smart Autonomous AI Controller for Snake Game.
Features:
1. Multi-Target Pathfinding: Evaluates golden bonus stars and all regular apples.
2. Precise Growth Simulation: Accurately simulates grow_pending delays so the snake
   never mistakes a stationary tail for a vacating space right after eating.
3. Box Method & Dead-End Pocket Pruning:
   - Evaluates connected open space for every prospective move.
   - Strictly forbids entering any enclosed pocket smaller than the snake's body length.
   - Detects 1-wide dead-end corridors and cul-de-sacs.
4. Longest-Path Tail Stalling & Boundary Hugging:
   - When food is unreachable or unsafe, stalls by taking the longest safe detour to the tail.
   - Hugs outer boundaries and existing coils, preventing the board from being bisected into traps.
"""

from collections import deque
from typing import Optional

# Directions
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
ALL_DIRECTIONS = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]


class SnakeAI:
    def __init__(self, grid_width: int = 30, grid_height: int = 24):
        self.width = grid_width
        self.height = grid_height

        # Loop / Repetition Detection & Human-Like Breakout
        self.history: deque[tuple[int, int]] = deque(maxlen=48)
        self.breakout_steps = 0
        self.last_eaten_count = 0

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = pos
        neighbors = []
        for dx, dy in ALL_DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        return neighbors

    def bfs_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        obstacles: set[tuple[int, int]],
    ) -> Optional[list[tuple[int, int]]]:
        """Finds shortest path from start to goal avoiding obstacles. Returns list of steps [next_pos, ..., goal]."""
        if start == goal:
            return []

        queue = deque([start])
        visited = {start}
        parent = {}

        while queue:
            current = queue.popleft()
            if current == goal:
                path = []
                curr = goal
                while curr != start:
                    path.append(curr)
                    curr = parent[curr]
                path.reverse()
                return path

            for neighbor in self.get_neighbors(current):
                if neighbor not in visited and (neighbor not in obstacles or neighbor == goal):
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        return None

    def flood_fill_score(self, start: tuple[int, int], obstacles: set[tuple[int, int]]) -> int:
        """Counts reachable open tiles from start (box size)."""
        if not self.in_bounds(start):
            return 0

        obs = obstacles - {start}
        queue = deque([start])
        visited = {start}
        count = 0

        while queue:
            curr = queue.popleft()
            count += 1
            for nxt in self.get_neighbors(curr):
                if nxt not in visited and nxt not in obs:
                    visited.add(nxt)
                    queue.append(nxt)

        return count

    def flood_fill_score_and_tail(
        self, start: tuple[int, int], tail: tuple[int, int], obstacles: set[tuple[int, int]]
    ) -> tuple[int, bool]:
        """Counts reachable open tiles from start, and whether the tail is inside the reachable area."""
        if not self.in_bounds(start):
            return 0, False

        obs = obstacles - {start}
        queue = deque([start])
        visited = {start}
        count = 0
        tail_reachable = (start == tail)

        while queue:
            curr = queue.popleft()
            count += 1
            if curr == tail:
                tail_reachable = True

            for nxt in self.get_neighbors(curr):
                if nxt not in visited and (nxt not in obs or nxt == tail):
                    visited.add(nxt)
                    queue.append(nxt)

        return count, tail_reachable

    def count_open_neighbors(self, pos: tuple[int, int], obstacles: set[tuple[int, int]]) -> int:
        """Counts how many adjacent cells are walkable."""
        open_count = 0
        for dx, dy in ALL_DIRECTIONS:
            nx, ny = pos[0] + dx, pos[1] + dy
            if self.in_bounds((nx, ny)) and (nx, ny) not in obstacles:
                open_count += 1
        return open_count

    def count_adjacent_obstacles(self, pos: tuple[int, int], obstacles: set[tuple[int, int]]) -> int:
        """Counts how many adjacent cells are walls or body segments (for boundary/wall hugging)."""
        x, y = pos
        adj = 0
        for dx, dy in ALL_DIRECTIONS:
            nx, ny = x + dx, y + dy
            if not self.in_bounds((nx, ny)) or (nx, ny) in obstacles:
                adj += 1
        return adj

    def simulate_and_check_tail_reachability(
        self,
        snake_body: list[tuple[int, int]],
        path_to_target: list[tuple[int, int]],
        grow_pending: int = 0,
        grow_amount: int = 1,
    ) -> bool:
        """
        Simulate moving a 'virtual snake' along the path to eat the target.
        Correctly accounts for grow_pending so the tail delay matches game engine reality!
        """
        virtual_body = list(snake_body)
        cur_pending = grow_pending
        target_step = path_to_target[-1]

        for step in path_to_target:
            virtual_body.insert(0, step)
            if step == target_step:
                cur_pending += grow_amount

            if cur_pending > 0:
                cur_pending -= 1
            else:
                virtual_body.pop()

        virtual_head = virtual_body[0]
        virtual_tail = virtual_body[-1]
        virtual_obstacles = set(virtual_body if cur_pending > 0 else virtual_body[:-1])

        # 1. Escape path from virtual head to virtual tail
        escape_path = self.bfs_path(virtual_head, virtual_tail, virtual_obstacles)
        if escape_path is None or len(escape_path) == 0:
            return False

        # 2. Box Method: Connected territory from virtual head
        box_size, has_tail = self.flood_fill_score_and_tail(virtual_head, virtual_tail, set(virtual_body[1:]))
        # If the box doesn't contain tail and is smaller than the snake, it's a closed pocket
        if not has_tail and box_size < len(virtual_body) + 2:
            return False

        # 3. Prevent entering narrow dead-end corridors
        if self.count_open_neighbors(virtual_head, virtual_obstacles) < 1:
            return False

        return True

    def get_safe_tail_move(
        self,
        head: tuple[int, int],
        tail: tuple[int, int],
        body: list[tuple[int, int]],
        grow_pending: int = 0,
    ) -> Optional[tuple[tuple[int, int], list[tuple[int, int]]]]:
        """
        Longest-Path & Box-Method Tail Chaser:
        Finds a safe neighbor move that preserves a path to the tail,
        maximizes open box territory, and takes the longest safe path to allow the tail to clear.
        """
        immediate_obstacles = set(body if grow_pending > 0 else body[:-1])
        valid_moves = []

        for dx, dy in ALL_DIRECTIONS:
            nxt = (head[0] + dx, head[1] + dy)
            if not self.in_bounds(nxt) or nxt in immediate_obstacles:
                continue

            # Simulate one step
            sim_body = [nxt] + (body if grow_pending > 0 else body[:-1])
            sim_tail = sim_body[-1]
            sim_pending = max(0, grow_pending - 1)
            sim_obs = set(sim_body if sim_pending > 0 else sim_body[:-1])

            # Path from nxt to tail
            path_to_tail = self.bfs_path(nxt, sim_tail, sim_obs)
            if path_to_tail is not None:
                box_size, has_tail = self.flood_fill_score_and_tail(nxt, sim_tail, sim_obs)

                # Dead-end pocket rejection:
                # If the box is smaller than the snake and doesn't lead out, reject!
                if not has_tail and box_size < len(body):
                    continue

                open_neighbors = self.count_open_neighbors(nxt, sim_obs)
                # Don't step into a dead end with 0 open exits
                if open_neighbors == 0 and nxt != sim_tail:
                    continue

                # Wall/body adjacency: hugging boundaries prevents cutting the board in half
                adjacency = self.count_adjacent_obstacles(nxt, set(body))
                path_len = len(path_to_tail)

                # Longest Path & Box Formula:
                # 1. Favor large connected box size
                # 2. Favor longer path to tail (gives tail more time to move!)
                # 3. Favor wall-hugging so the center of the board remains open
                base_score = box_size * 50 + path_len * 15 + adjacency * 3

                # Loop-breaking penalty: count how often nxt was recently visited
                revisit_count = self.history.count(nxt)
                if self.breakout_steps > 0:
                    # Decisive human-like breakout: completely avoid repeating cyclic tiles!
                    loop_penalty = revisit_count * 100000
                    unvisited_bonus = 10000 if revisit_count == 0 else 0
                else:
                    loop_penalty = revisit_count * 100
                    unvisited_bonus = 0

                final_score = base_score - loop_penalty + unvisited_bonus
                valid_moves.append(((dx, dy), path_to_tail, final_score))

        if valid_moves:
            valid_moves.sort(key=lambda item: item[2], reverse=True)
            chosen_dir, tail_path, _ = valid_moves[0]
            return chosen_dir, tail_path

        return None

    def get_emergency_survival_move(
        self,
        head: tuple[int, int],
        body: list[tuple[int, int]],
        grow_pending: int = 0,
    ) -> tuple[tuple[int, int], list[tuple[int, int]]]:
        """Emergency mode: Picks the move that gives the largest accessible box and avoids immediate dead ends."""
        immediate_obstacles = set(body if grow_pending > 0 else body[:-1])
        best_dir = None
        max_score = -1

        for dx, dy in ALL_DIRECTIONS:
            nxt = (head[0] + dx, head[1] + dy)
            if not self.in_bounds(nxt) or nxt in immediate_obstacles:
                continue

            box_size, _ = self.flood_fill_score_and_tail(nxt, body[-1], immediate_obstacles)
            open_exits = self.count_open_neighbors(nxt, immediate_obstacles)
            revisit_count = self.history.count(nxt)
            if self.breakout_steps > 0:
                revisit_penalty = revisit_count * 100000
            else:
                revisit_penalty = revisit_count * 50
            score = box_size * 10 + open_exits * 2 - revisit_penalty

            if score > max_score:
                max_score = score
                best_dir = (dx, dy)

        if best_dir is not None:
            return best_dir, []

        # Guaranteed collision fallback
        for dx, dy in ALL_DIRECTIONS:
            nxt = (head[0] + dx, head[1] + dy)
            if self.in_bounds(nxt):
                return (dx, dy), []

        return DIR_UP, []

    def get_next_move(
        self,
        snake_body: list[tuple[int, int]],
        food_pos: tuple[int, int] | list[tuple[int, int]],
        bonus_pos: Optional[tuple[int, int]] = None,
        bonus_active: bool = False,
        bonus_timer: float = 0.0,
        current_speed: float = 20.0,
        grow_pending: int = 0,
        fruits_eaten: int = 0,
    ) -> tuple[tuple[int, int], list[tuple[int, int]]]:
        """
        Master decision loop with Loop-Break Exploration, Longest-Path Stalling,
        Dead-End Prevention, and Box Method.
        """
        head = snake_body[0]
        tail = snake_body[-1]

        # 1. Reset loop tracking whenever fresh food was eaten
        if fruits_eaten != self.last_eaten_count:
            self.last_eaten_count = fruits_eaten
            self.history.clear()
            self.breakout_steps = 0

        # 2. Record head position & Detect repeated loop (3 to 5 times)
        self.history.append(head)
        times_visited = self.history.count(head)
        if times_visited >= 3:
            # Repeated 3+ times in recent window: trigger human-like breakout burst!
            self.breakout_steps = 16
        elif self.breakout_steps > 0:
            self.breakout_steps -= 1

        # Immediate obstacle check: if grow_pending > 0, tail won't vacate!
        immediate_obstacles = set(snake_body if grow_pending > 0 else snake_body[:-1])

        # Normalize foods to list
        if isinstance(food_pos, list):
            foods_list = food_pos
        else:
            foods_list = [food_pos]

        # 1. Check Bonus Star first if active and feasible
        if bonus_active and bonus_pos is not None:
            bonus_path = self.bfs_path(head, bonus_pos, immediate_obstacles)
            if bonus_path:
                time_needed = len(bonus_path) / max(current_speed, 1.0)
                if time_needed <= bonus_timer:
                    # Validate survival with growth timing
                    if self.simulate_and_check_tail_reachability(
                        snake_body, bonus_path, grow_pending=grow_pending, grow_amount=2
                    ):
                        first_step = bonus_path[0]
                        if first_step not in immediate_obstacles:
                            move_dir = (first_step[0] - head[0], first_step[1] - head[1])
                            return move_dir, bonus_path

        # 2. Check Regular Foods - find closest safely reachable food with Box validation
        safe_food_paths = []
        for fpos in foods_list:
            path = self.bfs_path(head, fpos, immediate_obstacles)
            if path:
                if self.simulate_and_check_tail_reachability(
                    snake_body, path, grow_pending=grow_pending, grow_amount=1
                ):
                    first_step = path[0]
                    if first_step not in immediate_obstacles:
                        # Dead-end check: don't take a first step into a dead end
                        if self.count_open_neighbors(first_step, immediate_obstacles) > 0 or first_step == fpos:
                            safe_food_paths.append((len(path), path))

        if safe_food_paths:
            if self.breakout_steps > 0:
                # Prefer food paths whose first step breaks out of the loop
                safe_food_paths.sort(key=lambda item: (self.history.count(item[1][0]), item[0]))
            else:
                safe_food_paths.sort(key=lambda item: item[0])
            best_path = safe_food_paths[0][1]
            first_step = best_path[0]
            move_dir = (first_step[0] - head[0], first_step[1] - head[1])
            return move_dir, best_path

        # 3. Food path is unsafe or blocked: Longest-Path & Box-Method Tail Chaser with Loop-Break
        tail_decision = self.get_safe_tail_move(head, tail, snake_body, grow_pending=grow_pending)
        if tail_decision is not None:
            chosen_dir, tail_path = tail_decision
            return chosen_dir, tail_path

        # 4. Emergency: Maximize open box territory
        return self.get_emergency_survival_move(head, snake_body, grow_pending=grow_pending)
