local M = {}

local defaults = {
  cli_path = "codemarshal",
  lint_on_save = true,
}

local namespace = vim.api.nvim_create_namespace("codemarshal")

local function normalize_path(path)
  if vim.loop.os_uname().sysname == "Windows_NT" then
    return string.lower(path)
  end
  return path
end

local function run_command(args)
  local cmd = table.concat(args, " ")
  local output = vim.fn.system(cmd)
  return output, vim.v.shell_error
end

local function apply_diagnostics(bufnr, matches)
  local diagnostics = {}
  for _, match in ipairs(matches) do
    local line = math.max(0, (match.line or 1) - 1)
    local severity = vim.diagnostic.severity.INFO
    if match.severity == "critical" then
      severity = vim.diagnostic.severity.ERROR
    elseif match.severity == "warning" then
      severity = vim.diagnostic.severity.WARN
    end
    table.insert(diagnostics, {
      lnum = line,
      col = 0,
      message = match.message or match.pattern_name or "CodeMarshal match",
      severity = severity,
      source = "CodeMarshal",
    })
  end
  vim.diagnostic.set(namespace, bufnr, diagnostics, {})
end

local function scan_file(config, file_path)
  local output, code = run_command({
    config.cli_path,
    "pattern",
    "scan",
    file_path,
    "--output=json",
  })
  if code ~= 0 and output == "" then
    vim.notify("CodeMarshal pattern scan failed", vim.log.levels.WARN)
    return
  end
  local ok, data = pcall(vim.json.decode, output)
  if not ok or not data then
    vim.notify("CodeMarshal: failed to parse JSON output", vim.log.levels.WARN)
    return
  end
  local matches = data.matches or {}
  local filtered = {}
  local target = normalize_path(file_path)
  for _, match in ipairs(matches) do
    if normalize_path(match.file) == target then
      table.insert(filtered, match)
    end
  end
  local bufnr = vim.fn.bufnr(file_path, true)
  apply_diagnostics(bufnr, filtered)
end

local function show_patterns(config)
  local file_path = vim.fn.expand("%:p")
  if file_path == "" then
    vim.notify("CodeMarshal: no file selected", vim.log.levels.WARN)
    return
  end
  local output, _ = run_command({
    config.cli_path,
    "pattern",
    "scan",
    file_path,
    "--output=json",
  })
  local ok, data = pcall(vim.json.decode, output)
  if not ok or not data then
    vim.notify("CodeMarshal: failed to parse JSON output", vim.log.levels.WARN)
    return
  end
  local lines = {
    "CodeMarshal Pattern Matches",
    string.rep("-", 40),
  }
  for _, match in ipairs(data.matches or {}) do
    table.insert(lines, string.format("%s:%s %s", match.file, match.line, match.message))
  end
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  local width = math.min(80, vim.o.columns - 4)
  local height = math.min(#lines + 2, vim.o.lines - 4)
  vim.api.nvim_open_win(buf, true, {
    relative = "editor",
    width = width,
    height = height,
    row = 2,
    col = 2,
    style = "minimal",
    border = "single",
  })
end

function M.setup(opts)
  local config = vim.tbl_extend("force", defaults, opts or {})

  vim.api.nvim_create_user_command("CodeMarshalInvestigate", function()
    local target = vim.fn.expand("%:p:h")
    if target == "" then
      vim.notify("CodeMarshal: no target selected", vim.log.levels.WARN)
      return
    end
    run_command({
      config.cli_path,
      "investigate",
      target,
      "--scope=module",
      "--intent=initial_scan",
    })
  end, {})

  vim.api.nvim_create_user_command("CodeMarshalPatterns", function()
    show_patterns(config)
  end, {})

  vim.keymap.set("n", "<leader>ci", ":CodeMarshalInvestigate<CR>")
  vim.keymap.set("n", "<leader>cp", ":CodeMarshalPatterns<CR>")

  if config.lint_on_save then
    vim.api.nvim_create_autocmd("BufWritePost", {
      pattern = { "*.py", "*.js", "*.ts", "*.java", "*.go" },
      callback = function()
        local file_path = vim.fn.expand("%:p")
        if file_path ~= "" then
          scan_file(config, file_path)
        end
      end,
    })
  end
end

return M
