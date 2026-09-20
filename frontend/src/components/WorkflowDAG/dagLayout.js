/**
 * dagLayout.js — Pure topological layout engine for workflow task DAGs.
 *
 * Accepts a flat tasks[] array (from the backend API) and returns positioned
 * node and edge objects ready for SVG rendering. No React dependency.
 *
 * Layout strategy: Left→Right layered digraph.
 *   - Column = topological depth from root tasks
 *   - Row    = position within column, vertically centered
 */

// ── Layout constants ────────────────────────────────────────────────────────
export const NODE_WIDTH   = 180;
export const NODE_HEIGHT  = 76;
export const COL_GAP      = 80;   // horizontal gap between column edges
export const ROW_GAP      = 24;   // vertical gap between nodes in same column
export const H_PADDING    = 32;   // left/right canvas padding
export const V_PADDING    = 32;   // top/bottom canvas padding

/**
 * Assign each task to a column (depth) via BFS from root tasks.
 * @param {Array} tasks
 * @returns {Map<string, number>}  taskName → column index
 */
function assignColumns(tasks) {
  const nameToTask = new Map(tasks.map((t) => [t.task_name, t]));
  const columns = new Map(); // taskName → column

  // BFS from all roots (tasks with no dependencies)
  const queue = [];
  for (const task of tasks) {
    if (!task.dependencies || task.dependencies.length === 0) {
      columns.set(task.task_name, 0);
      queue.push(task.task_name);
    }
  }

  // If no roots found (malformed data), assign all to column 0
  if (queue.length === 0) {
    tasks.forEach((t) => columns.set(t.task_name, 0));
    return columns;
  }

  let head = 0;
  while (head < queue.length) {
    const name = queue[head++];
    const col = columns.get(name);

    // Find tasks that list `name` as a dependency
    for (const task of tasks) {
      if (task.dependencies && task.dependencies.includes(name)) {
        const existing = columns.get(task.task_name);
        const newCol = col + 1;
        if (existing === undefined || existing < newCol) {
          columns.set(task.task_name, newCol);
          queue.push(task.task_name);
        }
      }
    }
  }

  // Fallback: any unvisited task goes to column 0
  for (const task of tasks) {
    if (!columns.has(task.task_name)) {
      columns.set(task.task_name, 0);
    }
  }

  return columns;
}

/**
 * dagLayout — compute node positions and edge paths from tasks[].
 *
 * @param {Array} tasks  — raw task objects from the backend
 * @returns {{ nodes: Array, edges: Array, svgWidth: number, svgHeight: number }}
 */
export function dagLayout(tasks) {
  if (!tasks || tasks.length === 0) {
    return { nodes: [], edges: [], svgWidth: 200, svgHeight: 100 };
  }

  // Step 1: assign columns
  const colMap = assignColumns(tasks);
  const numCols = Math.max(...colMap.values()) + 1;

  // Step 2: group tasks by column, sorted consistently
  const byColumn = Array.from({ length: numCols }, () => []);
  for (const task of tasks) {
    const col = colMap.get(task.task_name) ?? 0;
    byColumn[col].push(task);
  }

  // Step 3: compute canvas dimensions
  const colHeight = (col) =>
    col.length * NODE_HEIGHT + Math.max(0, col.length - 1) * ROW_GAP;

  const maxColHeight = Math.max(...byColumn.map(colHeight));
  const svgWidth  = H_PADDING * 2 + numCols * NODE_WIDTH + Math.max(0, numCols - 1) * COL_GAP;
  const svgHeight = V_PADDING * 2 + maxColHeight;

  // Step 4: assign x, y to each task
  const nameToCoords = new Map(); // taskName → { x, y, cx, cy }

  const nodes = [];
  for (let col = 0; col < byColumn.length; col++) {
    const colTasks = byColumn[col];
    const totalH = colHeight(colTasks);
    const startY = V_PADDING + (maxColHeight - totalH) / 2;
    const x = H_PADDING + col * (NODE_WIDTH + COL_GAP);

    colTasks.forEach((task, row) => {
      const y = startY + row * (NODE_HEIGHT + ROW_GAP);
      const cx = x + NODE_WIDTH / 2;
      const cy = y + NODE_HEIGHT / 2;

      nameToCoords.set(task.task_name, { x, y, cx, cy });

      nodes.push({
        task_id:       task.task_id,
        task_name:     task.task_name,
        agent:         task.agent,
        status:        task.status,
        retry_count:   task.retry_count ?? 0,
        max_retries:   task.max_retries ?? 3,
        error_message: task.error_message ?? null,
        result:        task.result ?? null,
        started_at:    task.started_at ?? null,
        completed_at:  task.completed_at ?? null,
        dependencies:  task.dependencies ?? [],
        x,
        y,
        cx,
        cy,
        col,
      });
    });
  }

  // Step 5: build edges
  const edges = [];
  for (const task of tasks) {
    if (!task.dependencies) continue;
    const target = nameToCoords.get(task.task_name);
    if (!target) continue;

    for (const depName of task.dependencies) {
      const source = nameToCoords.get(depName);
      if (!source) continue;

      // Edge starts at center-right of source node, ends at center-left of target
      const x1 = source.x + NODE_WIDTH;
      const y1 = source.cy;
      const x2 = target.x;
      const y2 = target.cy;

      // Control points for a smooth cubic bezier
      const cpOffset = Math.max(20, (x2 - x1) * 0.45);
      const cx1 = x1 + cpOffset;
      const cy1 = y1;
      const cx2 = x2 - cpOffset;
      const cy2 = y2;

      edges.push({
        id:         `edge-${depName}-${task.task_name}`,
        sourceName: depName,
        targetName: task.task_name,
        x1, y1, cx1, cy1, cx2, cy2, x2, y2,
      });
    }
  }

  return { nodes, edges, svgWidth, svgHeight };
}
