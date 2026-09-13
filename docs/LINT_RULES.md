# Bộ quy tắc Lint — Frontend & Backend

Tài liệu tổng hợp các rule linter đang được bật trong CI của dự án `cham-code`, tính đến ngày 2026-09-10.

## Tổng quan

| | Công cụ | Config | CI step | Số rule đang bật | Hành vi khi vi phạm |
|---|---|---|---|---|---|
| Frontend | ESLint (`eslint-config-next`) | [frontend/eslint.config.mjs](frontend/eslint.config.mjs) | `npm run lint` → `eslint --max-warnings=0` | 86 | error hoặc warning đều làm CI fail (nhờ `--max-warnings=0`) |
| Backend | Ruff | [backend/pyproject.toml](backend/pyproject.toml) | `ruff check .` | ~273 (rule stable) | mọi vi phạm đều làm `ruff check` exit ≠ 0 (không phân biệt warn/error) |

---

## Frontend — ESLint (86 rule)

Nguồn: preset `eslint-config-next` (`core-web-vitals` + `typescript`), áp cho toàn bộ code trong `frontend/`. Cột "Giải thích" dịch từ `meta.docs.description` gốc của từng rule, giữ nguyên các định danh code/từ khoá kỹ thuật.

### `core` (4 rule)

| Rule | Mức | Giải thích |
|---|---|---|
| `no-var` | error | Yêu cầu dùng `let` hoặc `const` thay vì `var` |
| `prefer-const` | error | Yêu cầu khai báo bằng `const` đối với biến không bị gán lại sau khi khai báo |
| `prefer-rest-params` | error | Yêu cầu dùng rest parameter thay vì `arguments` |
| `prefer-spread` | error | Yêu cầu dùng spread operator thay vì `.apply()` |

### `import` (1 rule)

| Rule | Mức | Giải thích |
|---|---|---|
| `import/no-anonymous-default-export` | warn | Cấm export mặc định (default export) một giá trị không có tên (anonymous) |

### `jsx-a11y` (6 rule) — Khả năng tiếp cận (Accessibility)

| Rule | Mức | Giải thích |
|---|---|---|
| `jsx-a11y/alt-text` | warn | Bắt buộc các phần tử cần văn bản thay thế (alt text) phải có nội dung có ý nghĩa để truyền tải cho người dùng cuối |
| `jsx-a11y/aria-props` | warn | Bắt buộc mọi prop `aria-*` phải hợp lệ |
| `jsx-a11y/aria-proptypes` | warn | Bắt buộc giá trị của các state/property ARIA phải hợp lệ |
| `jsx-a11y/aria-unsupported-elements` | warn | Bắt buộc các phần tử không hỗ trợ role/state/property ARIA thì không được gắn các thuộc tính đó |
| `jsx-a11y/role-has-required-aria-props` | warn | Bắt buộc phần tử có khai báo ARIA role phải có đầy đủ thuộc tính bắt buộc cho role đó |
| `jsx-a11y/role-supports-aria-props` | warn | Bắt buộc phần tử có role (khai báo tường minh hoặc ngầm định) chỉ được chứa các thuộc tính `aria-*` mà role đó hỗ trợ |

### `react` (17 rule) — Tính đúng đắn của React

| Rule | Mức | Giải thích |
|---|---|---|
| `react/display-name` | error | Cấm định nghĩa component React mà thiếu `displayName` |
| `react/jsx-key` | error | Cấm thiếu prop `key` khi render danh sách/collection literal |
| `react/jsx-no-comment-textnodes` | error | Cấm comment bị chèn nhầm thành text node trong JSX |
| `react/jsx-no-duplicate-props` | error | Cấm khai báo trùng property trong JSX |
| `react/jsx-no-undef` | error | Cấm dùng biến chưa khai báo trong JSX |
| `react/jsx-uses-react` | error | Cấm việc đánh dấu nhầm `React` là không dùng đến (unused) |
| `react/jsx-uses-vars` | error | Cấm việc đánh dấu nhầm các biến được dùng trong JSX là không dùng đến |
| `react/no-children-prop` | error | Cấm truyền `children` qua prop thông thường |
| `react/no-danger-with-children` | error | Cấm phần tử DOM dùng đồng thời `children` và `dangerouslySetInnerHTML` |
| `react/no-deprecated` | error | Cấm dùng các method đã deprecated |
| `react/no-direct-mutation-state` | error | Cấm mutate (thay đổi trực tiếp) `this.state` |
| `react/no-find-dom-node` | error | Cấm dùng `findDOMNode` |
| `react/no-is-mounted` | error | Cấm dùng `isMounted` |
| `react/no-render-return-value` | error | Cấm dùng giá trị trả về của `ReactDOM.render` |
| `react/no-string-refs` | error | Cấm dùng string ref (ref dạng chuỗi) |
| `react/no-unescaped-entities` | error | Cấm HTML entity chưa escape xuất hiện trong markup |
| `react/require-render-return` | error | Bắt buộc class ES5/ES6 phải `return` giá trị trong hàm `render` |

### `react-hooks` (16 rule)

| Rule | Mức | Giải thích |
|---|---|---|
| `react-hooks/config` | error | Kiểm tra tính hợp lệ của các tuỳ chọn cấu hình compiler |
| `react-hooks/error-boundaries` | error | Kiểm tra việc dùng error boundary thay vì try/catch để bắt lỗi từ component con |
| `react-hooks/exhaustive-deps` | warn | Kiểm tra danh sách dependency của các Hook như `useEffect` và tương tự |
| `react-hooks/gating` | error | Kiểm tra cấu hình của gating mode |
| `react-hooks/globals` | error | Kiểm tra việc gán/mutate biến global trong lúc render — side effect phải chạy ngoài render |
| `react-hooks/immutability` | error | Kiểm tra việc mutate props, state và các giá trị vốn phải bất biến (immutable) |
| `react-hooks/incompatible-library` | warn | Kiểm tra việc dùng các thư viện không tương thích với memoization (thủ công hoặc tự động) |
| `react-hooks/preserve-manual-memoization` | error | Kiểm tra compiler có giữ nguyên memoization thủ công đã có sẵn hay không |
| `react-hooks/purity` | error | Kiểm tra component/hook có pure (thuần khiết) hay không bằng cách xác nhận chúng không gọi hàm impure đã biết |
| `react-hooks/refs` | error | Kiểm tra việc dùng ref đúng cách, không đọc/ghi ref trong lúc render |
| `react-hooks/rules-of-hooks` | error | Bắt buộc tuân thủ Rules of Hooks |
| `react-hooks/set-state-in-effect` | error | Kiểm tra việc gọi `setState` đồng bộ bên trong effect |
| `react-hooks/set-state-in-render` | error | Kiểm tra việc set state trong lúc render, có thể gây render thừa hoặc vòng lặp vô hạn |
| `react-hooks/static-components` | error | Kiểm tra component có tĩnh (static) hay không, tránh bị tạo lại mỗi lần render |
| `react-hooks/unsupported-syntax` | warn | Kiểm tra các cú pháp mà React Compiler không có kế hoạch hỗ trợ |
| `react-hooks/use-memo` | error | Kiểm tra việc dùng hook `useMemo()` để tránh các lỗi thường gặp |

### `@next` (22 rule) — Đặc thù Next.js

| Rule | Mức | Giải thích |
|---|---|---|
| `@next/next/google-font-display` | warn | Bắt buộc khai báo hành vi `font-display` khi dùng Google Fonts |
| `@next/next/google-font-preconnect` | warn | Đảm bảo dùng `preconnect` khi tải Google Fonts |
| `@next/next/inline-script-id` | error | Bắt buộc component `next/script` có nội dung inline phải có thuộc tính `id` |
| `@next/next/next-script-for-ga` | warn | Ưu tiên dùng `@next/third-parties/google` thay vì script inline cho Google Analytics và Tag Manager |
| `@next/next/no-assign-module-variable` | error | Ngăn việc gán giá trị cho biến `module` |
| `@next/next/no-async-client-component` | warn | Ngăn Client Component được khai báo dưới dạng hàm async |
| `@next/next/no-before-interactive-script-outside-document` | warn | Ngăn dùng chiến lược `beforeInteractive` của `next/script` bên ngoài `pages/_document.js` |
| `@next/next/no-css-tags` | warn | Ngăn chèn thủ công thẻ stylesheet |
| `@next/next/no-document-import-in-page` | error | Ngăn import `next/document` bên ngoài `pages/_document.js` |
| `@next/next/no-duplicate-head` | error | Ngăn dùng trùng lặp `<Head>` trong `pages/_document.js` |
| `@next/next/no-head-element` | warn | Ngăn dùng thẻ `<head>` trực tiếp |
| `@next/next/no-head-import-in-document` | error | Ngăn dùng `next/head` trong `pages/_document.js` |
| `@next/next/no-html-link-for-pages` | error | Ngăn dùng thẻ `<a>` để điều hướng đến trang nội bộ của Next.js |
| `@next/next/no-img-element` | warn | Ngăn dùng thẻ `<img>` vì làm chậm LCP và tốn băng thông hơn |
| `@next/next/no-location-assign-relative-destination` | warn | Ngăn dùng `location.assign`/`location.href` để điều hướng đến trang nội bộ của Next.js |
| `@next/next/no-page-custom-font` | warn | Ngăn khai báo custom font chỉ ở phạm vi từng trang |
| `@next/next/no-script-component-in-head` | error | Ngăn dùng `next/script` bên trong component `next/head` |
| `@next/next/no-styled-jsx-in-document` | warn | Ngăn dùng `styled-jsx` trong `pages/_document.js` |
| `@next/next/no-sync-scripts` | error | Ngăn dùng script đồng bộ (blocking) |
| `@next/next/no-title-in-document-head` | warn | Ngăn dùng `<title>` cùng component `Head` từ `next/document` |
| `@next/next/no-typos` | warn | Ngăn các lỗi gõ sai (typo) thường gặp trong hàm fetch dữ liệu của Next.js |
| `@next/next/no-unwanted-polyfillio` | warn | Ngăn polyfill trùng lặp từ Polyfill.io |

### `@typescript-eslint` (20 rule)

| Rule | Mức | Giải thích |
|---|---|---|
| `@typescript-eslint/ban-ts-comment` | error | Cấm comment `@ts-<directive>` hoặc bắt buộc phải có mô tả sau directive |
| `@typescript-eslint/no-array-constructor` | error | Cấm dùng constructor `Array` kiểu generic |
| `@typescript-eslint/no-duplicate-enum-values` | error | Cấm giá trị trùng lặp giữa các thành viên enum |
| `@typescript-eslint/no-empty-object-type` | error | Cấm vô tình dùng kiểu "empty object" |
| `@typescript-eslint/no-explicit-any` | error | Cấm dùng kiểu `any` |
| `@typescript-eslint/no-extra-non-null-assertion` | error | Cấm dùng thừa non-null assertion (`!`) |
| `@typescript-eslint/no-misused-new` | error | Bắt buộc định nghĩa `new` và `constructor` hợp lệ |
| `@typescript-eslint/no-namespace` | error | Cấm dùng namespace của TypeScript |
| `@typescript-eslint/no-non-null-asserted-optional-chain` | error | Cấm dùng non-null assertion ngay sau optional chain (`?.`) |
| `@typescript-eslint/no-require-imports` | error | Cấm gọi `require()` |
| `@typescript-eslint/no-this-alias` | error | Cấm gán `this` cho một biến khác (alias) |
| `@typescript-eslint/no-unnecessary-type-constraint` | error | Cấm ràng buộc (constraint) không cần thiết trên generic type |
| `@typescript-eslint/no-unsafe-declaration-merging` | error | Cấm declaration merging không an toàn |
| `@typescript-eslint/no-unsafe-function-type` | error | Cấm dùng kiểu `Function` built-in không an toàn |
| `@typescript-eslint/no-unused-expressions` | warn | Cấm các expression không được sử dụng |
| `@typescript-eslint/no-unused-vars` | warn | Cấm khai báo biến rồi không dùng |
| `@typescript-eslint/no-wrapper-object-types` | error | Cấm dùng các class wrapper của kiểu nguyên thuỷ (primitive) built-in gây nhầm lẫn |
| `@typescript-eslint/prefer-as-const` | error | Bắt buộc dùng `as const` thay vì khai báo literal type |
| `@typescript-eslint/prefer-namespace-keyword` | error | Bắt buộc dùng từ khoá `namespace` thay vì `module` khi khai báo module TypeScript tuỳ chỉnh |
| `@typescript-eslint/triple-slash-reference` | error | Cấm một số triple-slash directive, thay bằng khai báo import kiểu ES6 |

### Frontend KHÔNG kiểm soát

- Format/style (thụt lề, dấu chấm phẩy...) — thuộc Prettier, chưa cấu hình trong repo.
- Logic nghiệp vụ hoặc test coverage — ESLint chỉ là static analysis, không thay test.
- Type error sâu (sai kiểu trả về hàm...) — việc này thuộc `tsc`, được che một phần nhờ bước `npm run build` trong CI.

---

## Backend — Ruff (~273 rule stable)

Nguồn: `select` tuỳ chỉnh trong [backend/pyproject.toml](backend/pyproject.toml) (`E, F, W, I, UP, B, C4, SIM, ASYNC, RUF`), `target-version = "py311"`. Cột "Giải thích" dịch từ `summary` gốc của Ruff (`ruff rule --all`), giữ nguyên định danh code; các placeholder dạng `{name}`, `{message}` là biến Ruff điền vào khi báo lỗi thật.

### `E` — pycodestyle errors (19 rule)

| Code | Giải thích |
|---|---|
| `E101` | Thụt lề lẫn lộn giữa space và tab |
| `E401` | Khai báo nhiều import trên cùng một dòng |
| `E402` | Import ở cấp module không nằm ở đầu file |
| `E501` | Dòng quá dài ({width} > {limit}) |
| `E701` | Nhiều statement trên cùng một dòng (dùng dấu `:`) |
| `E702` | Nhiều statement trên cùng một dòng (dùng dấu `;`) |
| `E703` | Statement kết thúc bằng dấu `;` không cần thiết |
| `E711` | So sánh với `None` nên viết thành `cond is None` |
| `E712` | Tránh so sánh bằng (`==`) với `True`; nên dùng `{cond}:` để kiểm tra truthy |
| `E713` | Kiểm tra thành viên nên dùng `not in` |
| `E714` | Kiểm tra định danh đối tượng nên dùng `is not` |
| `E721` | Dùng `is`/`is not` khi so sánh type, hoặc `isinstance()` khi kiểm tra kiểu instance |
| `E722` | Không dùng `except` trần (không chỉ định exception) |
| `E731` | Không gán biểu thức `lambda` cho biến, nên dùng `def` |
| `E741` | Tên biến dễ gây nhầm lẫn: `{name}` |
| `E742` | Tên class dễ gây nhầm lẫn: `{name}` |
| `E743` | Tên hàm dễ gây nhầm lẫn: `{name}` |
| `E902` | {message} (lỗi I/O khi đọc file) |
| `E999` | Lỗi cú pháp (SyntaxError) |

### `W` — pycodestyle warnings (6 rule)

| Code | Giải thích |
|---|---|
| `W191` | Thụt lề dùng tab |
| `W291` | Khoảng trắng thừa ở cuối dòng |
| `W292` | Thiếu newline ở cuối file |
| `W293` | Dòng trống nhưng chứa khoảng trắng |
| `W505` | Dòng docstring quá dài ({width} > {limit}) |
| `W605` | Escape sequence không hợp lệ: `\{ch}` |

### `F` — Pyflakes (43 rule)

| Code | Giải thích |
|---|---|
| `F401` | `{name}` được import nhưng không dùng |
| `F402` | Import `{name}` từ dòng {row} bị biến vòng lặp che khuất (shadow) |
| `F403` | Dùng `from {name} import *`; không thể xác định tên chưa định nghĩa |
| `F404` | Import `from __future__` phải đặt ở đầu file |
| `F405` | `{name}` có thể chưa được định nghĩa, hoặc được định nghĩa từ star import (`import *`) |
| `F406` | `from {name} import *` chỉ được phép dùng ở cấp module |
| `F407` | Future feature `{name}` không tồn tại |
| `F501` | Chuỗi format kiểu `%` không hợp lệ: {message} |
| `F502` | Chuỗi format kiểu `%` cần một mapping nhưng lại nhận một sequence |
| `F503` | Chuỗi format kiểu `%` cần một sequence nhưng lại nhận một mapping |
| `F504` | Chuỗi format kiểu `%` có tham số có tên (named argument) không được dùng: {message} |
| `F505` | Chuỗi format kiểu `%` thiếu tham số cho placeholder: {message} |
| `F506` | Chuỗi format kiểu `%` trộn lẫn placeholder theo vị trí và theo tên |
| `F507` | Chuỗi format kiểu `%` có {wanted} placeholder nhưng chỉ có {got} giá trị thay thế |
| `F508` | Specifier `*` trong chuỗi format kiểu `%` yêu cầu một sequence |
| `F509` | Chuỗi format kiểu `%` chứa ký tự định dạng không được hỗ trợ: `{char}` |
| `F521` | Lời gọi `.format` có chuỗi format không hợp lệ: {message} |
| `F522` | Lời gọi `.format` có tham số có tên không được dùng: {message} |
| `F523` | Lời gọi `.format` có tham số theo vị trí không được dùng: {message} |
| `F524` | Lời gọi `.format` thiếu tham số cho placeholder: {message} |
| `F525` | Chuỗi `.format` trộn lẫn đánh số tự động và thủ công |
| `F541` | f-string không chứa placeholder nào |
| `F601` | Key literal `{name}` bị lặp lại trong dictionary |
| `F602` | Key `{name}` bị lặp lại trong dictionary |
| `F621` | Quá nhiều expression trong phép gán star-unpacking |
| `F622` | Có hai starred expression trong cùng một phép gán |
| `F631` | Điều kiện `assert` là một tuple không rỗng, luôn luôn `True` |
| `F632` | Dùng `==` để so sánh các literal hằng số |
| `F633` | Dùng `>>` với hàm `print` là không hợp lệ |
| `F634` | Điều kiện `if` là một tuple, luôn luôn `True` |
| `F701` | `break` nằm ngoài vòng lặp |
| `F702` | `continue` không nằm đúng trong vòng lặp |
| `F704` | Statement `{keyword}` nằm ngoài hàm |
| `F706` | Statement `return` nằm ngoài hàm/method |
| `F707` | Khối `except` không phải handler cuối cùng |
| `F722` | Lỗi cú pháp trong forward annotation: {parse_error} |
| `F811` | Định nghĩa lại `{name}` (chưa dùng) từ dòng {row} |
| `F821` | Tên `{name}` chưa được định nghĩa. {tip} |
| `F822` | Tên `{name}` trong `__all__` chưa được định nghĩa |
| `F823` | Biến cục bộ `{name}` được tham chiếu trước khi gán giá trị |
| `F841` | Biến cục bộ `{name}` được gán giá trị nhưng không dùng |
| `F842` | Biến cục bộ `{name}` được annotate kiểu nhưng không dùng |
| `F901` | `raise NotImplemented` nên viết thành `raise NotImplementedError` |

### `I` — isort (2 rule)

| Code | Giải thích |
|---|---|
| `I001` | Khối import chưa được sắp xếp hoặc định dạng đúng chuẩn |
| `I002` | Thiếu import bắt buộc: `{name}` |

### `UP` — pyupgrade (47 rule)

| Code | Giải thích |
|---|---|
| `UP001` | `__metaclass__ = type` là mặc định, không cần khai báo |
| `UP003` | Dùng `{}` thay vì `type(...)` |
| `UP004` | Class `{name}` kế thừa từ `object` (không cần thiết ở Python 3) |
| `UP005` | `{alias}` đã deprecated, dùng `{target}` |
| `UP006` | Dùng `{to}` thay vì `{from}` khi annotate kiểu |
| `UP007` | Dùng `X \| Y` khi annotate kiểu |
| `UP008` | Dùng `super()` thay vì `super(__class__, self)` |
| `UP009` | Khai báo encoding UTF-8 ở đầu file là không cần thiết |
| `UP010` | Import `__future__` `{import}` không cần thiết với phiên bản Python mục tiêu |
| `UP011` | Dấu ngoặc thừa khi gọi `functools.lru_cache` |
| `UP012` | Gọi `encode` sang UTF-8 một cách không cần thiết |
| `UP013` | Chuyển `{name}` từ cú pháp `TypedDict` dạng hàm sang cú pháp class |
| `UP014` | Chuyển `{name}` từ cú pháp `NamedTuple` dạng hàm sang cú pháp class |
| `UP015` | Tham số `mode` không cần thiết |
| `UP017` | Dùng alias `datetime.UTC` |
| `UP018` | Gọi `{literal_type}` không cần thiết (nên viết lại thành literal) |
| `UP019` | `{}.Text` đã deprecated, dùng `str` |
| `UP020` | Dùng hàm `open` built-in |
| `UP021` | `universal_newlines` đã deprecated, dùng `text` |
| `UP022` | Ưu tiên dùng `capture_output` thay vì gán `stdout`/`stderr` là `PIPE` |
| `UP023` | `cElementTree` đã deprecated, dùng `ElementTree` |
| `UP024` | Thay các exception alias bằng `OSError` |
| `UP025` | Bỏ tiền tố unicode literal (`u"..."`) khỏi chuỗi |
| `UP026` | `mock` đã deprecated, dùng `unittest.mock` |
| `UP027` | Thay list comprehension unpack bằng generator expression |
| `UP028` | Thay `yield` trong vòng `for` bằng `yield from` |
| `UP029` | Import built-in không cần thiết: `{import}` |
| `UP030` | Dùng tham chiếu ngầm định cho field format theo vị trí |
| `UP031` | Dùng format specifier thay vì định dạng kiểu `%` |
| `UP032` | Dùng f-string thay vì gọi `.format()` |
| `UP033` | Dùng `@functools.cache` thay vì `@functools.lru_cache(maxsize=None)` |
| `UP034` | Tránh dấu ngoặc thừa |
| `UP035` | Nên import từ `{target}` thay vì vị trí hiện tại: {names} |
| `UP036` | Khối kiểm tra version đã lỗi thời so với phiên bản Python tối thiểu |
| `UP037` | Bỏ dấu ngoặc kép khỏi type annotation |
| `UP038` | Dùng `X \| Y` trong lời gọi `{}` thay vì `(X, Y)` |
| `UP039` | Dấu ngoặc thừa sau khai báo class |
| `UP040` | Type alias `{name}` dùng {type_alias_method} thay vì từ khoá `type` |
| `UP041` | Thay các exception alias bằng `TimeoutError` |
| `UP042` | Class {name} kế thừa đồng thời cả `str` và `enum.Enum` |
| `UP043` | Tham số kiểu mặc định không cần thiết |
| `UP044` | Dùng `*` để unpacking |
| `UP045` | Dùng `X \| None` khi annotate kiểu |
| `UP046` | Generic class `{name}` kế thừa `Generic` thay vì dùng type parameter |
| `UP047` | Hàm generic `{name}` nên dùng type parameter |
| `UP049` | Generic {} dùng type parameter private |
| `UP050` | Class `{name}` khai báo `metaclass=type`, thừa không cần thiết |

### `B` — flake8-bugbear (39 rule) — nhóm bắt bug thật

| Code | Giải thích |
|---|---|
| `B002` | Python không hỗ trợ toán tử tăng tiền tố (`++`) |
| `B003` | Gán trực tiếp vào `os.environ` không xoá được biến môi trường hiện có |
| `B004` | Dùng `hasattr(x, "__call__")` để kiểm tra x có gọi được hay không là không đáng tin cậy; nên dùng `callable(x)` |
| `B005` | Dùng `.strip()` với chuỗi nhiều ký tự dễ gây hiểu nhầm (strip theo từng ký tự, không phải chuỗi con) |
| `B006` | Không dùng cấu trúc dữ liệu mutable làm giá trị mặc định cho tham số |
| `B007` | Biến điều khiển vòng lặp `{name}` không được dùng trong thân vòng lặp |
| `B008` | Không gọi hàm `{name}` ngay trong giá trị mặc định của tham số |
| `B009` | Không gọi `getattr` với tên thuộc tính là hằng số |
| `B010` | Không gọi `setattr` với tên thuộc tính là hằng số |
| `B011` | Không dùng `assert False` (bị loại bỏ khi chạy `python -O`), nên `raise AssertionError()` |
| `B012` | `{name}` bên trong khối `finally` khiến exception bị nuốt (silenced) |
| `B013` | Tuple literal chỉ có một phần tử là thừa trong exception handler |
| `B014` | Exception handler khai báo trùng exception: `{name}` |
| `B015` | Phép so sánh vô nghĩa — có thể bạn định gán giá trị? |
| `B016` | Không thể `raise` một literal — có thể bạn định `return` nó hoặc raise một Exception? |
| `B017` | Không `assert` một exception mơ hồ (blind): `{exception}` |
| `B018` | Phát hiện expression vô dụng — hãy gán nó vào một biến hoặc xoá đi |
| `B019` | Dùng `functools.lru_cache`/`functools.cache` trên method có thể gây memory leak |
| `B020` | Biến điều khiển vòng lặp `{name}` ghi đè lên chính iterable đang được lặp |
| `B021` | Dùng f-string làm docstring — Python sẽ hiểu đây là chuỗi ghép, không phải docstring |
| `B022` | Không truyền tham số nào cho `contextlib.suppress` — context manager trở nên thừa |
| `B023` | Hàm định nghĩa bên trong vòng lặp không bind biến vòng lặp `{name}` — lỗi closure kinh điển |
| `B024` | `{name}` là abstract base class nhưng không có method/property abstract nào |
| `B025` | Khối try-except* khai báo trùng exception `{name}` |
| `B026` | Không nên dùng star-arg unpacking sau một keyword argument |
| `B027` | `{name}` là method rỗng trong abstract base class nhưng không có decorator abstract |
| `B028` | Không tìm thấy tham số `stacklevel` được truyền tường minh |
| `B029` | Dùng `except* ():` với tuple rỗng sẽ không bắt được exception nào |
| `B030` | Handler của `except*` chỉ nên là exception class hoặc tuple các exception class |
| `B031` | Dùng lại generator trả về từ `itertools.groupby()` lần thứ hai sẽ không có tác dụng gì |
| `B032` | Có thể vô tình viết thành type annotation (dùng `:`) — có phải bạn định gán giá trị (dùng `=`)? |
| `B033` | Set không nên chứa phần tử trùng lặp `{value}` |
| `B034` | `{method}` nên truyền `{param_name}` và `flags` dưới dạng keyword argument |
| `B035` | Dictionary comprehension dùng key tĩnh (cố định): `{key}` |
| `B039` | Không dùng cấu trúc dữ liệu mutable làm giá trị mặc định cho `ContextVar` |
| `B904` | Trong khối `except*`, hãy raise exception bằng `raise ... from err` hoặc `raise ... from None` |
| `B905` | `zip()` không truyền tường minh tham số `strict=` |
| `B911` | `itertools.batched()` không truyền tường minh tham số `strict` |
| `B912` | `map()` không truyền tường minh tham số `strict=` |

### `C4` — flake8-comprehensions (19 rule)

| Code | Giải thích |
|---|---|
| `C400` | Generator không cần thiết (nên viết lại bằng `list()`) |
| `C401` | Generator không cần thiết (nên viết lại bằng `set()`) |
| `C402` | Generator không cần thiết (nên viết lại thành dict comprehension) |
| `C403` | List comprehension không cần thiết (nên viết lại thành set comprehension) |
| `C404` | List comprehension không cần thiết (nên viết lại thành dict comprehension) |
| `C405` | Literal {kind} không cần thiết (nên viết lại thành set literal) |
| `C406` | Literal {obj_type} không cần thiết (nên viết lại thành dict literal) |
| `C408` | Gọi `{kind}()` không cần thiết (nên viết lại thành literal) |
| `C409` | Truyền list literal vào `tuple()` một cách không cần thiết |
| `C410` | Truyền list literal vào `list()` một cách không cần thiết |
| `C411` | Gọi `list()` không cần thiết |
| `C413` | Bọc `{func}()` quanh `sorted()` một cách không cần thiết |
| `C414` | Gọi `{inner}()` không cần thiết bên trong `{outer}()` |
| `C415` | Đảo ngược iterable bằng subscript một cách không cần thiết bên trong `{func}()` |
| `C416` | Comprehension {kind} không cần thiết (nên viết lại bằng `{kind}()`) |
| `C417` | Dùng `map()` không cần thiết (nên viết lại bằng {object_type}) |
| `C418` | Truyền {kind} dict vào `dict()` một cách không cần thiết |
| `C419` | List comprehension không cần thiết |
| `C420` | Dict comprehension không cần thiết cho iterable; nên dùng `dict.fromkeys` |

### `SIM` — flake8-simplify (30 rule)

| Code | Giải thích |
|---|---|
| `SIM101` | Gọi `isinstance` nhiều lần cho `{name}`, nên gộp thành một lời gọi |
| `SIM102` | Dùng một câu lệnh `if` duy nhất thay vì lồng nhiều `if` |
| `SIM103` | Return trực tiếp điều kiện `{condition}` |
| `SIM105` | Dùng `contextlib.suppress({exception})` thay vì `try`-`except`-`pass` |
| `SIM107` | Không dùng `return` đồng thời trong cả `try`-`except` và `finally` |
| `SIM108` | Dùng toán tử ba ngôi `{contents}` thay vì khối `if`-`else` |
| `SIM109` | Dùng `{replacement}` thay vì so sánh bằng nhiều lần |
| `SIM110` | Dùng `{replacement}` thay vì vòng lặp `for` |
| `SIM112` | Dùng biến môi trường viết hoa `{expected}` thay vì `{actual}` |
| `SIM113` | Dùng `enumerate()` cho biến chỉ số `{index}` trong vòng `for` |
| `SIM114` | Gộp các nhánh `if` bằng toán tử logic `or` |
| `SIM115` | Dùng context manager khi mở file |
| `SIM116` | Dùng dictionary thay vì nhiều câu lệnh `if` liên tiếp |
| `SIM117` | Dùng một câu lệnh `with` cho nhiều context thay vì lồng nhiều `with` |
| `SIM118` | Dùng `key {operator} dict` thay vì `key {operator} dict.keys()` |
| `SIM201` | Dùng `{left} != {right}` thay vì `not {left} == {right}` |
| `SIM202` | Dùng `{left} == {right}` thay vì `not {left} != {right}` |
| `SIM208` | Dùng `{expr}` thay vì `not (not {expr})` |
| `SIM210` | Bỏ cấu trúc `True if ... else False` không cần thiết |
| `SIM211` | Dùng `not ...` thay vì `False if ... else True` |
| `SIM212` | Dùng `{expr_else} if {expr_else} else {expr_body}` thay vì `{expr_body} if not {expr_else} else {expr_else}` |
| `SIM220` | Dùng `False` thay vì `{name} and not {name}` |
| `SIM221` | Dùng `True` thay vì `{name} or not {name}` |
| `SIM222` | Dùng `{expr}` thay vì `{replaced}` |
| `SIM223` | Dùng `{expr}` thay vì `{replaced}` |
| `SIM300` | Phát hiện điều kiện kiểu Yoda (hằng số đặt trước biến khi so sánh) |
| `SIM401` | Dùng `{contents}` thay vì một khối `if` |
| `SIM905` | Cân nhắc dùng list literal thay vì `str.{}` |
| `SIM910` | Dùng `{expected}` thay vì `{actual}` |
| `SIM911` | Dùng `{expected}` thay vì `{actual}` |

### `ASYNC` — flake8-async (15 rule) — đặc thù FastAPI

| Code | Giải thích |
|---|---|
| `ASYNC100` | Context `with {method_name}(...):` không chứa statement `await` nào — timeout trở nên vô nghĩa |
| `ASYNC105` | Lời gọi `{method_name}` không được `await` ngay lập tức |
| `ASYNC109` | Hàm async được định nghĩa với tham số `timeout` |
| `ASYNC110` | Dùng `{module}.Event` thay vì `await {module}.sleep` trong vòng lặp `while` |
| `ASYNC115` | Dùng `{module}.lowlevel.checkpoint()` thay vì `{module}.sleep(0)` |
| `ASYNC116` | `{module}.sleep()` với khoảng thời gian >24 giờ thường nên là `{module}.sleep_forever()` |
| `ASYNC210` | Hàm async không nên gọi các HTTP method chặn đồng bộ (blocking) |
| `ASYNC212` | Gọi method httpx chặn đồng bộ {name}.{call}() trong ngữ cảnh async, nên dùng `httpx.AsyncClient` |
| `ASYNC220` | Hàm async không nên tạo subprocess bằng method chặn đồng bộ |
| `ASYNC221` | Hàm async không nên chạy process bằng method chặn đồng bộ |
| `ASYNC222` | Hàm async không nên chờ process bằng method chặn đồng bộ |
| `ASYNC230` | Hàm async không nên mở file bằng method chặn đồng bộ như `open` |
| `ASYNC240` | Hàm async không nên thực hiện thao tác {path_library} chặn đồng bộ |
| `ASYNC250` | Gọi `input()` (chặn đồng bộ) trong ngữ cảnh async |
| `ASYNC251` | Hàm async không nên gọi `time.sleep` |

### `RUF` — Ruff-specific (53 rule)

| Code | Giải thích |
|---|---|
| `RUF001` | Chuỗi chứa ký tự dễ gây nhầm lẫn {}. Có phải bạn muốn dùng {}? |
| `RUF002` | Docstring chứa ký tự dễ gây nhầm lẫn {}. Có phải bạn muốn dùng {}? |
| `RUF003` | Comment chứa ký tự dễ gây nhầm lẫn {}. Có phải bạn muốn dùng {}? |
| `RUF005` | Cân nhắc dùng `{expression}` thay vì nối chuỗi/nối danh sách (concatenation) |
| `RUF006` | Nên lưu lại tham chiếu đến giá trị trả về của `{expr}.{method}` |
| `RUF007` | Ưu tiên dùng `itertools.pairwise()` thay vì `zip()` khi lặp qua các cặp phần tử liên tiếp |
| `RUF008` | Không dùng giá trị mặc định mutable cho thuộc tính của dataclass |
| `RUF009` | Không gọi hàm `{name}` trong giá trị mặc định của dataclass |
| `RUF010` | Dùng conversion flag tường minh (`!r`, `!s`...) |
| `RUF011` | Dictionary comprehension dùng key tĩnh (cố định) |
| `RUF012` | Giá trị mặc định mutable cho thuộc tính của class |
| `RUF013` | PEP 484 không cho phép `Optional` ngầm định |
| `RUF015` | Ưu tiên dùng `next({iterable})` thay vì slice lấy một phần tử |
| `RUF016` | Slice khi truy cập theo chỉ số vào kiểu `{value_type}` dùng kiểu `{index_type}` thay vì số nguyên |
| `RUF017` | Tránh cộng dồn list theo kiểu có độ phức tạp bậc hai (quadratic) |
| `RUF018` | Tránh dùng assignment expression (`:=`) trong câu lệnh `assert` |
| `RUF019` | Kiểm tra key không cần thiết trước khi truy cập dictionary |
| `RUF020` | `{never_like} \| T` tương đương với `T` |
| `RUF021` | Nên đặt trong ngoặc `a and b` khi kết hợp `and`/`or` liên tiếp để rõ ràng thứ tự ưu tiên |
| `RUF022` | `__all__` chưa được sắp xếp |
| `RUF023` | `{}.__slots__` chưa được sắp xếp |
| `RUF024` | Không truyền object mutable làm giá trị cho `dict.fromkeys` |
| `RUF026` | `default_factory` là tham số chỉ nhận theo vị trí (positional-only) của `defaultdict` |
| `RUF028` | Comment suppression này không hợp lệ vì {} |
| `RUF030` | Gọi `print()` trong câu lệnh `assert` có khả năng là không cố ý |
| `RUF032` | `Decimal()` được gọi với tham số là float literal |
| `RUF033` | Method `__post_init__` có tham số mang giá trị mặc định |
| `RUF034` | Điều kiện `if`-`else` vô nghĩa |
| `RUF035` | Phát hiện cách dùng `{name}` không an toàn |
| `RUF036` | `None` không nằm ở cuối type union |
| `RUF037` | Iterable rỗng không cần thiết trong lời gọi `deque` |
| `RUF040` | Dùng literal không phải chuỗi làm message cho `assert` |
| `RUF041` | `Literal` lồng nhau không cần thiết |
| `RUF043` | Pattern truyền vào `match=` chứa ký tự đặc biệt (metacharacter) nhưng chưa escape hoặc chưa dùng raw string |
| `RUF046` | Giá trị được cast sang `int` vốn đã là số nguyên |
| `RUF048` | `__version__` có thể chứa phần tử không giống số nguyên |
| `RUF049` | Class enum không nên gắn decorator `@dataclass` |
| `RUF051` | Dùng `pop` thay vì kiểm tra `key in dict` rồi `del dict[key]` |
| `RUF053` | Class có khai báo type parameter list nhưng vẫn kế thừa `Generic` |
| `RUF057` | Giá trị được `round` vốn đã là số nguyên |
| `RUF058` | `itertools.starmap` được gọi trên iterable từ `zip` |
| `RUF059` | Biến `{name}` được unpack nhưng không dùng |
| `RUF060` | Kiểm tra thành viên (membership test) không cần thiết trên collection rỗng |
| `RUF061` | Dùng dạng context manager của `pytest.{}()` |
| `RUF063` | Dùng `{suggestion}` thay vì truy cập `__dict__` |
| `RUF064` | Giá trị `mode` không ở dạng bát phân (octal) |
| `RUF068` | `__all__` chứa phần tử trùng lặp |
| `RUF100` | Directive `# noqa` không còn cần thiết (không có lỗi nào để bỏ qua) |
| `RUF101` | `{original}` được chuyển hướng (redirect) sang `{target}` |
| `RUF102` | Mã rule không hợp lệ trong {}: {} |
| `RUF103` | Comment suppression không hợp lệ: {msg} |
| `RUF104` | Comment suppression không có comment `#ruff:enable` tương ứng để đóng lại |
| `RUF200` | Không parse được `pyproject.toml`: {message} |

### Backend KHÔNG kiểm soát

- Type checking (`mypy`/`pyright`) — chưa có trong repo.
- Format thống nhất — `ruff format --check` chưa được bật trong CI (quyết định tạm thời, có thể bật sau).
- Test/coverage — `pytest` đang bị comment trong CI ([.github/workflows/ci.yaml](.github/workflows/ci.yaml)), chờ có test thật.

---

## Ghi chú

- Danh sách rule ở trên là bản chụp tại thời điểm viết tài liệu (`ruff 0.16.6`, `eslint-config-next 16.3.4`). Khi nâng version các package này, số lượng/nội dung rule có thể thay đổi — nên chạy lại `ruff rule --all` / `eslint --print-config` nếu cần đối chiếu.
- Cột "Giải thích" của backend giữ nguyên placeholder dạng `{name}`, `{message}`... vì đó là biến Ruff điền vào khi báo lỗi thật (ví dụ `{name}` sẽ hiện tên biến/hàm cụ thể vi phạm).
- Rule `preview` (chưa stable) của Ruff không được tính vào danh sách trên vì mặc định chưa bật.
