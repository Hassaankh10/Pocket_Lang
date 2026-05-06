# PocketLang — DFA Diagrams & Parse Tree Examples

CS4031 — Compiler Construction, Spring 2026

---

## Part 1 — Lexer DFA (Deterministic Finite Automaton)

The PocketLang lexer is a hand-written scanner that implements the following DFA. Each state is labeled; transitions are labeled with the character class that triggers them. `*` denotes an accepting state; transitions back to `START` consume the current character and emit a token.

### State legend

| State       | Description                                      |
|-------------|--------------------------------------------------|
| `START`     | Initial / between tokens                         |
| `IDENT`     | Reading an identifier or keyword                 |
| `INT`       | Reading integer digits                           |
| `FLOAT`     | Reading fraction digits after the decimal point  |
| `DOT_SEEN`  | Saw `.` after digits — must see at least one digit|
| `COMMENT`   | Inside `// …` comment (until end-of-line)        |
| `LT_SEEN`   | Saw `<` — next may be `=`                        |
| `GT_SEEN`   | Saw `>` — next may be `=`                        |
| `EQ_SEEN`   | Saw `=` — next may be `=`                        |
| `BANG_SEEN` | Saw `!` — next must be `=`                       |
| `SLASH_SEEN`| Saw `/` — next may be `/` (comment) or emit `OP` |
| `ERROR`     | Unrecognised character                           |

### DFA transition table

```
                    letter/  digit   '.'   '/'   '<'   '>'   '='   '!'  other  '\n'  EOF
                    '_'
  ──────────────────────────────────────────────────────────────────────────────────────────
  START           → IDENT    INT     err   SLASH LT    GT    EQ    BANG  *emit  skip  EOF*
  IDENT           → IDENT    IDENT   *kw   *kw   *kw   *kw   *kw   *kw   *kw    *kw   *kw
  INT             → *ident   INT     DOT   *num  *num  *num  *num  *num  *num   *num  *num
  DOT_SEEN        → err      FLOAT   err   err   err   err   err   err   err    err   err
  FLOAT           → *float   FLOAT   *fl   *fl   *fl   *fl   *fl   *fl   *fl    *fl   *fl
  SLASH_SEEN      → *op/     *op/    *op/  COMMEN*op/  *op/  *op/  *op/  *op/   *op/  *op/
  COMMENT         → COMMENT  COMMENT CMT   CMT   CMT   CMT   CMT   CMT   CMT   START  EOF*
  LT_SEEN         → *'<'     *'<'    *'<'  *'<'  *'<'  *'<'  *'<=' *'<'  *'<'  *'<'  *'<'
  GT_SEEN         → *'>'     *'>'    *'>'  *'>'  *'>'  *'>'  *'>=' *'>'  *'>'  *'>'  *'>'
  EQ_SEEN         → *'='     *'='    *'='  *'='  *'='  *'='  *'==' *'='  *'='  *'='  *'='
  BANG_SEEN       → err      err     err   err   err   err   *'!=' err   err    err   err
```

`*kw` = check identifier string against keyword table; emit KEYWORD or IDENT.
`*num` = un-consume the character, emit INT token.
`*float` = un-consume the character, emit FLOAT token.
`*op/` = un-consume, emit SLASH operator.
`err` = emit LEXER_ERROR.

### DFA diagram (ASCII art)

```
                        ┌──────────────────────────────────────────────┐
                        │                     START                     │
                        └───┬──────────┬──────────┬────┬────┬────┬─────┘
                  letter/_  │  digit   │  '/'     │'<' │'>' │'=' │'!'
                            ▼          ▼           ▼    ▼    ▼    ▼
                          IDENT       INT      SLASH  LT  GT  EQ  BANG
                         ┌──┐        ┌──┐     ┌──┐
                    self  │  │  digit │  │ '/' │  │──────────────► COMMENT ──'\n'──► START
              (letter/digit)◄─┘       │  │     └──┘           (any)◄──┘
                  *IDENT/KW           │  │ else: *SLASH
                                      │  │
                                   '.'│  │
                                      ▼  │
                                    DOT  │
                                      │  │
                                 digit│  │ digit self
                                      ▼  ▼
                                    FLOAT ◄──┐
                                    *FLOAT   │(digit)
                                             │
                          LT ──'='──► *LE    │
                          GT ──'='──► *GE    │
                          EQ ──'='──► *EQEQ  │
                          BANG──'='──► *NEQ   │
                          (else: *single-char op)
```

---

## Part 2 — Parse Tree Examples

The parser builds an AST using recursive descent. Below are two examples showing the tree produced for concrete PocketLang programs.

### Example 1 — Expression: `2 * 3 + 4`

**Source:**
```
print 2 * 3 + 4
```

**Parse derivation (top-down):**
```
program
  └─ statement → print_stmt
       └─ "print"  expression
                     └─ equality
                          └─ comparison
                               └─ term
                                    ├─ factor          [left operand of '+']
                                    │    ├─ unary
                                    │    │    └─ primary → INT_LIT(2)
                                    │    ├─ '*'
                                    │    └─ unary
                                    │         └─ primary → INT_LIT(3)
                                    ├─ '+'
                                    └─ factor          [right operand of '+']
                                         └─ unary
                                              └─ primary → INT_LIT(4)
```

**AST (as printed by `--debug=ast`):**
```
PrintStmt
  BinOp(+)
    BinOp(*)
      Literal(2)
      Literal(3)
    Literal(4)
```

After constant folding the IR reduces to a single `PRINT 10`.

---

### Example 2 — `if` / `else` with comparison

**Source:**
```
let x = 5
if x > 3 {
    print x
} else {
    print 0
}
```

**Parse tree:**
```
program
  ├─ statement → let_stmt
  │    ├─ "let"  IDENT("x")  "="
  │    └─ expression
  │         └─ equality → comparison → term → factor → unary
  │              └─ primary → INT_LIT(5)
  │
  └─ statement → if_stmt
       ├─ "if"
       ├─ expression (condition)
       │    └─ equality
       │         └─ comparison
       │              ├─ term → factor → unary → primary → IDENT("x")
       │              ├─ '>'
       │              └─ term → factor → unary → primary → INT_LIT(3)
       ├─ block (then)
       │    └─ statement → print_stmt
       │         └─ expression → … → IDENT("x")
       └─ block (else)
            └─ statement → print_stmt
                 └─ expression → … → INT_LIT(0)
```

**AST (as printed by `--debug=ast`):**
```
LetStmt(x)
  Literal(5)
IfStmt
  BinOp(>)
    Name(x)
    Literal(3)
  Block
    PrintStmt
      Name(x)
  Block
    PrintStmt
      Literal(0)
```

---

### Example 3 — Function call: `fib(n - 1)`

**Source (fragment):**
```
return fib(n - 1) + fib(n - 2)
```

**Parse tree:**
```
statement → return_stmt
  └─ expression
       └─ equality → comparison
            └─ term
                 ├─ factor → unary → primary
                 │    └─ call → IDENT("fib")  "("
                 │         └─ expression (arg 1)
                 │              └─ … → term
                 │                       ├─ factor → unary → primary → IDENT("n")
                 │                       ├─ '-'
                 │                       └─ factor → unary → primary → INT_LIT(1)
                 ├─ '+'
                 └─ factor → unary → primary
                      └─ call → IDENT("fib")  "("
                           └─ expression (arg 1)
                                └─ … → term
                                         ├─ factor → … → IDENT("n")
                                         ├─ '-'
                                         └─ factor → … → INT_LIT(2)
```

**AST:**
```
ReturnStmt
  BinOp(+)
    Call(fib)
      BinOp(-)
        Name(n)
        Literal(1)
    Call(fib)
      BinOp(-)
        Name(n)
        Literal(2)
```

---

## Part 3 — Symbol Table Walkthrough

For the program:

```
let x = 10
func double(a) {
    let result = a * 2
    return result
}
let y = double(x)
print y
```

Symbol table at each phase:

**After `let x = 10` (global scope):**
```
Scope[global]
  x → { type: int, value: 10 }
```

**Inside `func double` body:**
```
Scope[global]
  x        → { type: int }
  double   → { kind: func, params: [a], defined: true }

  Scope[double]
    a      → { type: int, param: true }
    result → { type: int }
```

**After full analysis:**
```
Scope[global]
  x      → { type: int }
  double → { kind: func, params: ['a'] }
  y      → { type: int }
```

The `--debug=symtab` flag prints the complete table after semantic analysis.
