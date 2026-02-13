# CodeMarshal Neovim Plugin

## Setup

```lua
require("codemarshal").setup({
  cli_path = "codemarshal",
  lint_on_save = true,
})
```

## Commands

- `:CodeMarshalInvestigate` - run investigation on current file directory
- `:CodeMarshalPatterns` - scan patterns for current file and show a floating window

## Keymaps

- `<leader>ci` - investigate
- `<leader>cp` - scan patterns
