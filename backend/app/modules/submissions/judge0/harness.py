import math
import json
import re

from app.core.exceptions import InvalidFormatError
from app.core import config

REQUIRED_HARNESS_LANGUAGES = ("python", "javascript")
OPTIONAL_HARNESS_LANGUAGES = ("c", "cpp")
HARNESS_LANGUAGES = REQUIRED_HARNESS_LANGUAGES + OPTIONAL_HARNESS_LANGUAGES
ALL_STARTER_LANGUAGES = ("python", "c", "cpp", "java", "javascript")

RESULT_MARKER = "\n@@CHAM_CODE_RESULT@@"
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

FLOAT_REL_TOL = 1e-9
FLOAT_ABS_TOL = 1e-9

_PYTHON_DRIVER = '''
import json as _json
import sys as _sys

def _cham_main():
    _args = _json.loads(_sys.stdin.read())
    _fn = globals().get({name!r})
    if _fn is None and "Solution" in globals():
        _fn = getattr(globals()["Solution"](), {name!r})
    _real_stdout = _sys.stdout
    _sys.stdout = _sys.stderr
    try:
        _result = _fn(*_args)
    finally:
        _sys.stdout = _real_stdout
    _real_stdout.write({marker!r} + _json.dumps(_result, separators=(",", ":"), ensure_ascii=False))
    _real_stdout.flush()

_cham_main()
'''

_JS_DRIVER = """
;(function () {{
  const __args = JSON.parse(require("fs").readFileSync(0, "utf8"));
  const __fn = typeof {name} === "function" ? {name} : null;
  const __log = console.log;
  console.log = function () {{}};
  let __result;
  try {{
    __result = __fn(...__args);
  }} finally {{
    console.log = __log;
  }}
  process.stdout.write({marker} + JSON.stringify(__result === undefined ? null : __result));
}})();
"""


def supports_function_harness(language: str) -> bool:
    return language in HARNESS_LANGUAGES


def build_source(
    language: str, student_code: str, function_name: str, starter_code: str | None = None,
) -> str:
    if not _IDENTIFIER.match(function_name):
        raise ValueError("function_name không hợp lệ")
    if language == "python":
        driver = _PYTHON_DRIVER.format(name=function_name, marker=RESULT_MARKER)
        return f"{student_code}\n{driver}"
    if language == "javascript":
        driver = _JS_DRIVER.format(name=function_name, marker=json.dumps(RESULT_MARKER))
        return f"{student_code}\n{driver}"
    if language == "c":
        return build_c_function_source(student_code, function_name, starter_code or "")
    if language == "cpp":
        return build_cpp_function_source(student_code, function_name, starter_code or "")
    raise ValueError(f"Chưa hỗ trợ function harness cho {language}")


def extract_result(stdout: str | None) -> str | None:
    """Lấy JSON kết quả sau marker; None nếu chương trình không in ra marker."""
    if not stdout or RESULT_MARKER not in stdout:
        return None
    return stdout.rsplit(RESULT_MARKER, 1)[1]


def _values_match(expected, actual) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if isinstance(expected, int) and isinstance(actual, int):
            return expected == actual
        return math.isclose(expected, actual, rel_tol=FLOAT_REL_TOL, abs_tol=FLOAT_ABS_TOL)
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(map(_values_match, expected, actual))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(
            _values_match(value, actual[key]) for key, value in expected.items()
        )
    return type(expected) is type(actual) and expected == actual


def json_outputs_match(expected_json: str, actual_json: str | None) -> bool:
    if actual_json is None:
        return False
    try:
        return _values_match(json.loads(expected_json), json.loads(actual_json))
    except ValueError:
        return False


def text_outputs_match(expected: str, actual: str | None) -> bool:
    return (actual or "").strip() == expected.strip()

_CPP_RUNTIME = r'''#include <bits/stdc++.h>
using namespace std;
namespace __cham {
struct J {
  enum Kind { Null, Bool, Number, String, Array, Object } kind = Null;
  bool boolean = false;
  string scalar;
  vector<J> array;
  map<string, J> object;
};
struct Parser {
  string source; size_t pos = 0;
  explicit Parser(string s) : source(std::move(s)) {}
  void ws() { while (pos < source.size() && isspace((unsigned char)source[pos])) ++pos; }
  string str() {
    if (source.at(pos++) != '"') throw runtime_error("expected string");
    string out;
    while (pos < source.size()) {
      char c = source[pos++];
      if (c == '"') return out;
      if (c != '\\') { out += c; continue; }
      if (pos >= source.size()) throw runtime_error("bad escape");
      char e = source[pos++];
      if (e == '"' || e == '\\' || e == '/') out += e;
      else if (e == 'b') out += '\b'; else if (e == 'f') out += '\f';
      else if (e == 'n') out += '\n'; else if (e == 'r') out += '\r'; else if (e == 't') out += '\t';
      else if (e == 'u') {
        unsigned cp = 0;
        for (int i = 0; i < 4; ++i) {
          if (pos >= source.size()) throw runtime_error("bad unicode escape");
          char h = source[pos++]; cp <<= 4;
          if (h >= '0' && h <= '9') cp |= h - '0'; else if (h >= 'a' && h <= 'f') cp |= h - 'a' + 10;
          else if (h >= 'A' && h <= 'F') cp |= h - 'A' + 10; else throw runtime_error("bad unicode escape");
        }
        if (cp < 0x80) out += char(cp);
        else if (cp < 0x800) { out += char(0xC0 | (cp >> 6)); out += char(0x80 | (cp & 63)); }
        else { out += char(0xE0 | (cp >> 12)); out += char(0x80 | ((cp >> 6) & 63)); out += char(0x80 | (cp & 63)); }
      } else throw runtime_error("bad escape");
    }
    throw runtime_error("unterminated string");
  }
  J value() {
    ws(); if (pos >= source.size()) throw runtime_error("empty JSON");
    J out; char c = source[pos];
    if (c == '"') { out.kind = J::String; out.scalar = str(); return out; }
    if (c == '[') {
      ++pos; out.kind = J::Array; ws(); if (pos < source.size() && source[pos] == ']') { ++pos; return out; }
      while (true) { out.array.push_back(value()); ws(); if (source.at(pos++) == ']') break; if (source.at(pos - 1) != ',') throw runtime_error("bad array"); }
      return out;
    }
    if (c == '{') {
      ++pos; out.kind = J::Object; ws(); if (pos < source.size() && source[pos] == '}') { ++pos; return out; }
      while (true) { ws(); string key = str(); ws(); if (source.at(pos++) != ':') throw runtime_error("bad object"); out.object.emplace(key, value()); ws(); char sep = source.at(pos++); if (sep == '}') break; if (sep != ',') throw runtime_error("bad object"); }
      return out;
    }
    if (source.compare(pos, 4, "true") == 0) { pos += 4; out.kind = J::Bool; out.boolean = true; return out; }
    if (source.compare(pos, 5, "false") == 0) { pos += 5; out.kind = J::Bool; return out; }
    if (source.compare(pos, 4, "null") == 0) { pos += 4; return out; }
    size_t start = pos; if (source[pos] == '-') ++pos;
    while (pos < source.size() && (isdigit((unsigned char)source[pos]) || source[pos] == '.' || source[pos] == 'e' || source[pos] == 'E' || source[pos] == '+' || source[pos] == '-')) ++pos;
    if (start == pos) throw runtime_error("bad value");
    out.kind = J::Number; out.scalar = source.substr(start, pos - start); return out;
  }
};
inline string quote(const string& s) {
  string out = "\""; const char* hex = "0123456789abcdef";
  for (unsigned char c : s) { if (c == '"' || c == '\\') { out += '\\'; out += char(c); }
    else if (c == '\n') out += "\\n"; else if (c == '\r') out += "\\r"; else if (c == '\t') out += "\\t";
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; } else out += char(c); }
  return out + "\"";
}
template<class T> struct is_vec : false_type {};
template<class T, class A> struct is_vec<vector<T, A>> : true_type { using value_type = T; };
template<class T> using bare_t = remove_cv_t<remove_reference_t<T>>;
template<class T> T from(const J& j) {
  if constexpr (is_same_v<T, string>) { if (j.kind != J::String) throw runtime_error("expected string"); return j.scalar; }
  else if constexpr (is_same_v<T, char>) { if (j.kind == J::String && !j.scalar.empty()) return j.scalar[0]; return static_cast<char>(stoll(j.scalar)); }
  else if constexpr (is_same_v<T, bool>) { if (j.kind == J::Bool) return j.boolean; return j.scalar == "1" || j.scalar == "true"; }
  else if constexpr (is_integral_v<T>) { if (j.kind == J::Bool) return T(j.boolean); return static_cast<T>(stoll(j.scalar)); }
  else if constexpr (is_floating_point_v<T>) return static_cast<T>(stold(j.scalar));
  else if constexpr (is_vec<T>::value) { T out; for (const auto& item : j.array) out.push_back(from<typename is_vec<T>::value_type>(item)); return out; }
  else if constexpr (is_pointer_v<T>) {
    using E = remove_cv_t<remove_pointer_t<T>>;
    if constexpr (is_same_v<E, char>) { string s = j.scalar; auto* p = new char[s.size() + 1]; memcpy(p, s.c_str(), s.size() + 1); return p; }
    else { auto* p = new E[j.array.size()]; for (size_t i = 0; i < j.array.size(); ++i) p[i] = from<E>(j.array[i]); return p; }
  } else static_assert(sizeof(T) == 0, "Unsupported C++ testcase parameter type");
}
template<class T> string to(const T& v) {
  using U = decay_t<T>;
  if constexpr (is_same_v<U, string>) return quote(v);
  else if constexpr (is_same_v<U, char>) return quote(string(1, v));
  else if constexpr (is_same_v<U, bool>) return v ? "true" : "false";
  else if constexpr (is_integral_v<U>) return to_string(v);
  else if constexpr (is_floating_point_v<U>) { if (!isfinite(v)) return "null"; ostringstream s; s << setprecision(17) << v; return s.str(); }
  else if constexpr (is_vec<U>::value) { string out = "["; bool first = true; for (const auto& item : v) { if (!first) out += ","; first = false; out += to(static_cast<typename is_vec<U>::value_type>(item)); } return out + "]"; }
  else if constexpr (is_pointer_v<U>) { if (!v) return "null"; if constexpr (is_same_v<remove_cv_t<remove_pointer_t<U>>, char>) return quote(string(v)); else return "null"; }
  else return "null";
}
template<class> struct traits;
template<class R, class C, class... A> struct traits<R(C::*)(A...)> { using result = R; using args = tuple<A...>; };
template<class R, class C, class... A> struct traits<R(C::*)(A...) const> { using result = R; using args = tuple<A...>; };
template<class R, class... A> struct traits<R(*)(A...)> { using result = R; using args = tuple<A...>; };
template<class F, class C, size_t... I> string method(F f, C& self, const vector<J>& input, index_sequence<I...>) {
  using T = traits<F>; using A = typename T::args; using R = typename T::result;
  if (input.size() != sizeof...(I)) throw runtime_error("wrong argument count");
  tuple<bare_t<tuple_element_t<I, A>>...> args{from<bare_t<tuple_element_t<I, A>>>(input[I])...};
  if constexpr (is_void_v<R>) { apply([&](auto&... x) { (self.*f)(x...); }, args); return "null"; }
  else if constexpr (is_pointer_v<R> && !is_same_v<remove_cv_t<remove_pointer_t<R>>, char>) throw runtime_error("C++ pointer returns need a length-bearing container such as vector");
  else { auto result = apply([&](auto&... x) { return (self.*f)(x...); }, args); return to(result); }
}
template<class F, size_t... I> string global(F f, const vector<J>& input, index_sequence<I...>) {
  using T = traits<F>; using A = typename T::args; using R = typename T::result;
  if (input.size() != sizeof...(I)) throw runtime_error("wrong argument count");
  tuple<bare_t<tuple_element_t<I, A>>...> args{from<bare_t<tuple_element_t<I, A>>>(input[I])...};
  if constexpr (is_void_v<R>) { apply([&](auto&... x) { f(x...); }, args); return "null"; }
  else if constexpr (is_pointer_v<R> && !is_same_v<remove_cv_t<remove_pointer_t<R>>, char>) throw runtime_error("C++ pointer returns need a length-bearing container such as vector");
  else { auto result = apply([&](auto&... x) { return f(x...); }, args); return to(result); }
}
template<class F, class C> string call_method(F f, C& self, const vector<J>& args) { return method(f, self, args, make_index_sequence<tuple_size<typename traits<F>::args>::value>{}); }
template<class F> string call_global(F f, const vector<J>& args) { return global(f, args, make_index_sequence<tuple_size<typename traits<F>::args>::value>{}); }
}
'''


def _parse_cpp_signature(
    starter_code: str,
    function_name: str,
) -> tuple[str, list[tuple[str, str, bool]]] | None:
    signature = re.search(
        rf"(?P<prefix>[^;{{}}]*?)\b{re.escape(function_name)}\s*\("
        rf"(?P<params>[^()]*(?:\([^()]*\)[^()]*)*)\)\s*"
        rf"(?:const\s*)?(?:noexcept(?:\s*\([^)]*\))?\s*)?(?:;|\{{)",
        starter_code,
        re.S,
    )
    if signature is None:
        return None
    return_type = re.sub(r"(?m)^\s*#.*$", "", signature.group("prefix"))
    return_type = re.sub(r"/\*.*?\*/|//[^\n]*", "", return_type, flags=re.S)
    return_type = re.sub(r"\b(public|private|protected)\s*:\s*", " ", return_type)
    return_type = re.sub(r"\b(static|inline|virtual|constexpr|friend|explicit)\b", "", return_type)
    return_type = " ".join(return_type.split())
    if not return_type:
        raise InvalidFormatError(f"Không suy ra được kiểu trả về C++ của '{function_name}'")

    parameters: list[tuple[str, str, bool]] = []
    for declaration in _split_c_parameters(signature.group("params")):
        declaration = re.sub(r"\s*=\s*[^,]+$", "", declaration).strip()
        array_suffix = bool(re.search(r"(?:\s*\[[^]]*\])+$", declaration))
        if array_suffix:
            declaration = re.sub(r"(?:\s*\[[^]]*\])+$", "", declaration).strip()
        name_match = re.search(r"([A-Za-z_]\w*)$", declaration)
        if name_match is None:
            raise InvalidFormatError(f"Không phân tích được tham số C++: {declaration}")
        name = name_match.group(1)
        type_name = declaration[:name_match.start()].strip()
        if not type_name:
            raise InvalidFormatError(f"Không phân tích được kiểu tham số C++: {declaration}")
        parameters.append((type_name, name, array_suffix))
    return return_type, parameters


def _cpp_parameter_type(type_name: str, is_array: bool) -> str:
    normalized = re.sub(r"\b(const|volatile)\b", "", type_name).strip()
    normalized = re.sub(r"&&?$", "", normalized).strip()
    if is_array:
        normalized += " *"
    return " ".join(normalized.split())


def _cpp_is_array_parameter(type_name: str, is_array: bool) -> bool:
    normalized = _cpp_parameter_type(type_name, is_array)
    if re.search(r"\bchar\s*\*", normalized):
        return False
    return is_array or "*" in normalized or re.search(r"\b(?:std::)?vector\s*<", normalized) is not None


def _build_cpp_size_aware_main(
    function_name: str,
    owner: str | None,
    signature: tuple[str, list[tuple[str, str, bool]]],
) -> str | None:
    return_type, parameters = signature
    return_size_index: int | None = None
    for index, (type_name, name, _is_array) in enumerate(parameters):
        if name.lower() == "returnsize":
            size_parameter_type = _cpp_parameter_type(type_name, False)
            if index != len(parameters) - 1 or size_parameter_type.count("*") != 1:
                raise InvalidFormatError("returnSize phải là tham số con trỏ cuối cùng trong chữ ký C++")
            return_size_index = index

    array_size_sources: dict[int, int] = {}
    for size_index, (_type_name, size_name, _is_array) in enumerate(parameters):
        if size_index == return_size_index or not size_name.lower().endswith("size"):
            continue
        array_name = size_name[:-4].lower()
        for array_index in range(size_index):
            array_type, candidate_name, candidate_array = parameters[array_index]
            if candidate_name.lower() == array_name and _cpp_is_array_parameter(array_type, candidate_array):
                array_size_sources[size_index] = array_index
                break

    if not array_size_sources and return_size_index is None:
        return None

    json_slots: dict[int, int] = {}
    slot = 0
    for index in range(len(parameters)):
        if index == return_size_index or index in array_size_sources:
            continue
        json_slots[index] = slot
        slot += 1

    declarations: list[str] = []
    arguments: list[str] = []
    array_checks: list[str] = []
    return_size_var: str | None = None
    for index, (type_name, _name, is_array) in enumerate(parameters):
        variable = f"__cham_arg_{index}"
        parameter_type = _cpp_parameter_type(type_name, is_array)
        if index == return_size_index:
            size_type = parameter_type.replace("*", "").strip()
            if not re.fullmatch(
                r"(?:(?:unsigned|signed)\s+)?(?:char|short|int|long(?:\s+long)?|size_t|std::size_t)",
                size_type,
            ):
                raise InvalidFormatError(f"Kiểu returnSize C++ chưa được hỗ trợ: {type_name}")
            return_size_var = "__cham_return_size"
            declarations.append(f"{size_type} {return_size_var} = 0; {size_type} *{variable} = &{return_size_var};")
            arguments.append(variable)
        elif index in array_size_sources:
            size_type = parameter_type
            if not re.fullmatch(
                r"(?:(?:unsigned|signed)\s+)?(?:char|short|int|long(?:\s+long)?|size_t|std::size_t)",
                size_type,
            ):
                raise InvalidFormatError(f"Kiểu tham số độ dài mảng C++ chưa được hỗ trợ: {type_name}")
            source_slot = json_slots[array_size_sources[index]]
            array_checks.append(f"root.array[{source_slot}].kind != __cham::J::Array")
            declarations.append(f"{size_type} {variable} = static_cast<{size_type}>(root.array[{source_slot}].array.size());")
            arguments.append(variable)
        else:
            source_slot = json_slots[index]
            if _cpp_is_array_parameter(type_name, is_array):
                array_checks.append(f"root.array[{source_slot}].kind != __cham::J::Array")
            from_type = parameter_type
            declarations.append(f"auto {variable} = __cham::from<{from_type}>(root.array[{source_slot}]);")
            arguments.append(variable)

    object_declaration = f"{owner} solution;" if owner else ""
    call = (
        f"solution.{function_name}({', '.join(arguments)})"
        if owner
        else f"{function_name}({', '.join(arguments)})"
    )
    normalized_return = " ".join(re.sub(r"\b(const|volatile)\b", "", return_type).split())
    pointer_return = "*" in normalized_return
    char_pointer_return = re.search(r"\bchar\s*\*", normalized_return) is not None
    if normalized_return.count("*") > 1:
        raise InvalidFormatError(f"Function harness C++ chưa hỗ trợ nhiều cấp con trỏ: {return_type}")
    if return_size_var is not None and not pointer_return:
        raise InvalidFormatError("returnSize chỉ dùng với hàm trả về con trỏ mảng trong C++")
    if pointer_return and not char_pointer_return and return_size_var is None:
        raise InvalidFormatError("Hàm C++ trả về con trỏ mảng cần tham số returnSize cuối để serialize kết quả")

    if normalized_return == "void":
        result_output = f'{call}; cout << "\\n@@CHAM_CODE_RESULT@@null";'
    elif return_size_var is not None and not char_pointer_return:
        result_output = (
            f"auto __cham_result = {call}; "
            f'if ({return_size_var} < 0) '
            'throw runtime_error("returnSize cannot be negative"); '
            f'cout << "\\n@@CHAM_CODE_RESULT@@"; '
            f'if (!__cham_result && {return_size_var} > 0) '
            'throw runtime_error("null array result with positive returnSize"); '
            'cout << "["; for (int __i = 0; __i < ' + return_size_var + '; ++__i) { if (__i) cout << ","; cout << __cham::to(__cham_result[__i]); } cout << "]";'
        )
    else:
        result_output = f'auto __cham_result = {call}; cout << "\\n@@CHAM_CODE_RESULT@@" << __cham::to(__cham_result);'

    checks = " || ".join(array_checks)
    checks = f" || {checks}" if checks else ""
    return f'''\nint main() {{\n  try {{ __cham::Parser p(string(istreambuf_iterator<char>(cin), {{}})); auto root = p.value();\n    if (root.kind != __cham::J::Array || root.array.size() != {slot}{checks}) throw runtime_error("wrong argument count or array argument type");\n    {object_declaration} {' '.join(declarations)}\n    {result_output}\n  }} catch (const exception& e) {{ cerr << e.what(); return 1; }}\n}}\n'''


def build_cpp_function_source(student_code: str, function_name: str, starter_code: str) -> str:
    if not starter_code.strip():
        raise InvalidFormatError("Function mode C++ cần starter_codes.cpp để suy ra chữ ký hàm")
    if function_name == "main":
        raise InvalidFormatError("function_name 'main' không dùng được với function harness C++")
    source_hint = starter_code + "\n" + student_code
    owner: str | None = None
    for class_match in re.finditer(r"\b(class|struct)\s+([A-Za-z_]\w*)\s*\{", source_hint):
        opening = source_hint.find("{", class_match.start())
        depth = 0
        closing = opening
        for closing in range(opening, len(source_hint)):
            if source_hint[closing] == "{":
                depth += 1
            elif source_hint[closing] == "}":
                depth -= 1
                if depth == 0:
                    break
        if depth == 0 and re.search(rf"\b{re.escape(function_name)}\s*\(", source_hint[opening:closing]):
            owner = class_match.group(2)
            break
    try:
        signature = _parse_cpp_signature(starter_code, function_name)
    except InvalidFormatError:
        if re.search(
            rf"\b{re.escape(function_name)}\s*\([^)]*(?:\b[A-Za-z_]\w*Size\b|\breturnSize\b)",
            starter_code,
        ):
            raise
        signature = None
    if signature is None and re.search(
        rf"\b{re.escape(function_name)}\s*\([^)]*(?:\b[A-Za-z_]\w*Size\b|\breturnSize\b)",
        starter_code,
    ):
        raise InvalidFormatError("Không phân tích được chữ ký C++ có tham số độ dài mảng hoặc returnSize")
    if signature is not None:
        size_aware_main = _build_cpp_size_aware_main(function_name, owner, signature)
        if size_aware_main is not None:
            return _CPP_RUNTIME + "\n" + student_code + "\n" + size_aware_main
    if owner is not None:
        main = f'''\nint main() {{\n  try {{ __cham::Parser p(string(istreambuf_iterator<char>(cin), {{}})); auto root = p.value();\n    if (root.kind != __cham::J::Array) throw runtime_error("input must be an argument array");\n    {owner} solution; auto result = __cham::call_method(&{owner}::{function_name}, solution, root.array);\n    cout << "\\n@@CHAM_CODE_RESULT@@" << result;\n  }} catch (const exception& e) {{ cerr << e.what(); return 1; }}\n}}\n'''
    else:
        if not re.search(rf"\b{re.escape(function_name)}\s*\(", source_hint):
            raise InvalidFormatError(f"Không tìm thấy chữ ký C++ cho function_name '{function_name}' trong starter_codes.cpp")
        if function_name == "main":
            raise InvalidFormatError("function_name 'main' không dùng được với function harness C++")
        main = f'''\nint main() {{\n  try {{ __cham::Parser p(string(istreambuf_iterator<char>(cin), {{}})); auto root = p.value();\n    if (root.kind != __cham::J::Array) throw runtime_error("input must be an argument array");\n    auto result = __cham::call_global(&{function_name}, root.array);\n    cout << "\\n@@CHAM_CODE_RESULT@@" << result;\n  }} catch (const exception& e) {{ cerr << e.what(); return 1; }}\n}}\n'''
    return _CPP_RUNTIME + "\n" + student_code + "\n" + main


def _split_c_parameters(parameters: str) -> list[str]:
    if not parameters.strip() or parameters.strip() == "void":
        return []
    parts: list[str] = []
    start = depth = 0
    for index, char in enumerate(parameters):
        if char in "(<[":
            depth += 1
        elif char in ")>]":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(parameters[start:index].strip())
            start = index + 1
    parts.append(parameters[start:].strip())
    return parts


def _parse_c_signature(starter_code: str, function_name: str) -> tuple[str, list[tuple[str, str]]]:
    match = re.search(rf"(?P<prefix>[^;{{}}]*?)\b{re.escape(function_name)}\s*\((?P<params>[^()]*(?:\([^()]*\)[^()]*)*)\)\s*(?:;|\{{)", starter_code, re.S)
    if match is None:
        raise InvalidFormatError(f"Không tìm thấy chữ ký C cho function_name '{function_name}' trong starter_codes.c")
    prefix = re.sub(r"(?m)^\s*#.*$", "", match.group("prefix"))
    prefix = re.sub(r"/\*.*?\*/|//[^\n]*", "", prefix, flags=re.S)
    return_type = re.sub(r"\b(static|inline|extern|register)\b", "", prefix).strip()
    if not return_type:
        raise InvalidFormatError(f"Không suy ra được kiểu trả về C của '{function_name}'")
    parameters: list[tuple[str, str]] = []
    for declaration in _split_c_parameters(match.group("params")):
        if declaration in {"...", "*"}:
            raise InvalidFormatError("C function harness không hỗ trợ variadic functions")
        parameter = re.fullmatch(
            r"(?P<type>(?:const\s+)?[A-Za-z_][\w\s]*?\s*(?:\*+\s*)?)\s*(?P<name>[A-Za-z_]\w*)\s*(?P<array>\[[^]]*\])?",
            declaration,
        )
        if parameter is None:
            raise InvalidFormatError(f"Không phân tích được tham số C: {declaration}")
        type_name = " ".join(parameter.group("type").split())
        if parameter.group("array"):
            type_name += " *"
        parameters.append((type_name, parameter.group("name")))
    return " ".join(return_type.split()), parameters


_C_RUNTIME = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
typedef struct J { int type; char *s; struct J **a; int n; } J;
static const char *cur;
static void ws(void) { while (*cur && isspace((unsigned char)*cur)) ++cur; }
static char *copy_range(const char *a, const char *b) { size_t n=(size_t)(b-a); char *s=(char*)malloc(n+1); memcpy(s,a,n); s[n]=0; return s; }
static int hexv(char c) { if(c>='0'&&c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10; if(c>='A'&&c<='F')return c-'A'+10; return -1; }
static void put_utf8(char *s,size_t *n,unsigned cp) { if(cp<0x80)s[(*n)++]=(char)cp; else if(cp<0x800){s[(*n)++]=(char)(0xC0|(cp>>6));s[(*n)++]=(char)(0x80|(cp&63));} else if(cp<0x10000){s[(*n)++]=(char)(0xE0|(cp>>12));s[(*n)++]=(char)(0x80|((cp>>6)&63));s[(*n)++]=(char)(0x80|(cp&63));} else {s[(*n)++]=(char)(0xF0|(cp>>18));s[(*n)++]=(char)(0x80|((cp>>12)&63));s[(*n)++]=(char)(0x80|((cp>>6)&63));s[(*n)++]=(char)(0x80|(cp&63));} }
static J *parse(void) {
  ws(); J *v=(J*)calloc(1,sizeof(J));
  if (*cur=='[') { ++cur; v->type=4; ws(); while (*cur && *cur!=']') { v->a=(J**)realloc(v->a,(v->n+1)*sizeof(J*)); v->a[v->n++]=parse(); ws(); if (*cur==',') {++cur; continue;} break; } if (*cur==']') ++cur; return v; }
  if (*cur=='"') { ++cur; char *s=(char*)malloc(strlen(cur)+1); size_t n=0; while (*cur && *cur!='"') { if (*cur=='\\' && cur[1]) { ++cur; char e=*cur++; if(e=='u'){unsigned cp=0;for(int i=0;i<4;++i){int h=hexv(*cur++);if(h<0)return v;cp=(cp<<4)|(unsigned)h;}if(cp>=0xD800&&cp<=0xDBFF&&cur[0]=='\\'&&cur[1]=='u'){cur+=2;unsigned lo=0;for(int i=0;i<4;++i){int h=hexv(*cur++);if(h<0)return v;lo=(lo<<4)|(unsigned)h;}if(lo>=0xDC00&&lo<=0xDFFF)cp=0x10000+((cp-0xD800)<<10)+(lo-0xDC00);}put_utf8(s,&n,cp);}else s[n++]=e=='n'?'\n':e=='r'?'\r':e=='t'?'\t':e=='b'?'\b':e=='f'?'\f':e; } else s[n++]=*cur++; } if (*cur=='"') ++cur; s[n]=0; v->type=3; v->s=s; return v; }
  const char *start=cur; while (*cur && !strchr(",]} \r\n\t",*cur)) ++cur; v->s=copy_range(start,cur); if (!strcmp(v->s,"true")||!strcmp(v->s,"false")) v->type=2; else if (!strcmp(v->s,"null")) v->type=0; else v->type=1; return v;
}
static long long ji(J *v) { return v->type==2 ? !strcmp(v->s,"true") : strtoll(v->s?v->s:"0",NULL,10); }
static double jd(J *v) { return v->type==2 ? !strcmp(v->s,"true") : strtod(v->s?v->s:"0",NULL); }
static char *js(J *v) { return v->s?v->s:""; }
static void qstr(const char *s) { static const char *hex="0123456789abcdef"; putchar('"'); for (;*s;++s) { unsigned char c=(unsigned char)*s; if (c=='"'||c=='\\') {putchar('\\');putchar(c);} else if (c=='\n') fputs("\\n",stdout); else if (c=='\r') fputs("\\r",stdout); else if (c=='\t') fputs("\\t",stdout); else if(c=='\b')fputs("\\b",stdout); else if(c=='\f')fputs("\\f",stdout); else if(c<0x20){fputs("\\u00",stdout);putchar(hex[c>>4]);putchar(hex[c&15]);} else putchar(c); } putchar('"'); }
'''


def _c_type_kind(type_name: str) -> str:
    normalized = re.sub(r"\b(const|volatile|restrict|static)\b", "", type_name).strip()
    if "*" in normalized:
        if re.fullmatch(r"char\s*\*\s*\*", normalized):
            return "string_array"
        if "char" in normalized:
            return "string"
        return "array"
    if "char" in normalized:
        return "char"
    if "float" in normalized or "double" in normalized:
        return "number"
    if "bool" in normalized or "_Bool" in normalized:
        return "bool"
    if any(word in normalized for word in ("int", "short", "long", "size_t", "uint")):
        return "integer"
    raise InvalidFormatError(f"Kiểu C chưa được hỗ trợ trong function harness: {type_name}")


def build_c_function_source(student_code: str, function_name: str, starter_code: str) -> str:
    if not starter_code.strip():
        raise InvalidFormatError("Function mode C cần starter_codes.c để suy ra chữ ký hàm")
    if function_name == "main":
        raise InvalidFormatError("function_name 'main' không dùng được với function harness C")
    return_type, parameters = _parse_c_signature(starter_code, function_name)
    consumed = 0
    declarations: list[str] = []
    arguments: list[str] = []
    array_slot_checks: list[str] = []
    size_vars: dict[str, str] = {}
    return_size_name: str | None = None
    for index, (type_name, name) in enumerate(parameters):
        normalized_type = re.sub(r"\b(const|volatile|restrict)\b", "", type_name).strip()
        is_string_array = re.fullmatch(r"char\s*\*\s*\*", normalized_type) is not None
        if normalized_type.count("*") > 1 and not is_string_array:
            raise InvalidFormatError(f"Function harness C chưa hỗ trợ nhiều cấp con trỏ: {type_name}")
        if "*" in normalized_type and "size" in name.lower() and index == len(parameters) - 1:
            return_size_name = name
            size_type = re.sub(r"\*+", "", normalized_type).strip()
            declarations.append(f"{size_type} {name} = 0;")
            arguments.append(f"&{name}")
            continue
        if name.lower() in {f"{array_name.lower()}size" for array_name in size_vars}:
            array_name = next(array_name for array_name in size_vars if name.lower() == f"{array_name.lower()}size")
            declarations.append(f"int {name} = __cham_input->a[{size_vars[array_name]}]->n;")
            arguments.append(name)
            continue
        kind = _c_type_kind(type_name)
        if kind == "array":
            slot = str(consumed)
            array_slot_checks.append(f"__cham_input->a[{slot}]->type != 4")
            base_type = re.sub(r"\*+", "", normalized_type).strip()
            c_scalar = re.sub(r"\b(const|volatile|restrict)\b", "", base_type).strip()
            if not re.fullmatch(r"(?:unsigned\s+|signed\s+)?(?:char|short|int|long(?:\s+long)?|float|double|size_t|_Bool|bool)", c_scalar):
                raise InvalidFormatError(f"Kiểu mảng C chưa được hỗ trợ trong function harness: {type_name}")
            var = f"__arg_{index}"
            declarations.append(f"{c_scalar} *{var} = (__cham_input->a[{slot}]->n ? ({c_scalar}*)malloc(__cham_input->a[{slot}]->n * sizeof({c_scalar})) : NULL);")
            conversion = "jd" if c_scalar in {"float", "double"} else "ji"
            declarations.append(f"for (int __i=0; __i<__cham_input->a[{slot}]->n; ++__i) {var}[__i] = ({c_scalar}){conversion}(__cham_input->a[{slot}]->a[__i]);")
            arguments.append(var)
            size_vars[name] = slot
            consumed += 1
        elif kind == "string_array":
            slot = str(consumed)
            array_slot_checks.append(f"__cham_input->a[{slot}]->type != 4")
            var = f"__arg_{index}"
            declarations.append(f"char **{var} = (__cham_input->a[{slot}]->n ? (char**)malloc(__cham_input->a[{slot}]->n * sizeof(char*)) : NULL);")
            declarations.append(f"for (int __i=0; __i<__cham_input->a[{slot}]->n; ++__i) {{ if (__cham_input->a[{slot}]->a[__i]->type != 3) return 2; {var}[__i] = js(__cham_input->a[{slot}]->a[__i]); }}")
            arguments.append(var)
            size_vars[name] = slot
            consumed += 1
        elif kind == "string":
            var = f"__arg_{index}"
            declarations.append(f"char *{var} = js(__cham_input->a[{consumed}]);")
            arguments.append(var)
            consumed += 1
        elif kind in {"integer", "char", "bool"}:
            var = f"__arg_{index}"
            c_type = re.sub(r"\b(const|volatile|restrict)\b", "", normalized_type).strip()
            if not re.fullmatch(r"(?:unsigned\s+|signed\s+)?(?:char|short|int|long(?:\s+long)?|_Bool|bool)", c_type):
                raise InvalidFormatError(f"Kiểu tham số C chưa được hỗ trợ trong function harness: {type_name}")
            conv = (
                f"(char)js(__cham_input->a[{consumed}])[0]"
                if kind == "char"
                else f"({c_type})ji(__cham_input->a[{consumed}])"
            )
            declarations.append(f"{c_type} {var} = {conv};")
            arguments.append(var)
            consumed += 1
        else:
            var = f"__arg_{index}"
            declarations.append(f"double {var} = jd(__cham_input->a[{consumed}]);")
            arguments.append(var)
            consumed += 1

    if re.sub(r"\b(static|inline|extern|register|const|volatile)\b", "", return_type).strip() == "void":
        ret_kind = "void"
    else:
        ret_kind = _c_type_kind(return_type)
    if ret_kind == "string_array":
        raise InvalidFormatError("C function harness chưa hỗ trợ trả về mảng chuỗi")
    call = f"{function_name}({', '.join(arguments)})"
    if ret_kind == "array":
        if return_size_name is None:
            raise InvalidFormatError("C function trả mảng cần tham số outputSize cuối để serialize kết quả")
        if return_type.count("*") > 1:
            raise InvalidFormatError(f"Function harness C chưa hỗ trợ nhiều cấp con trỏ: {return_type}")
        ret_base = re.sub(r"\b(const|volatile|restrict)\b", "", re.sub(r"\*+", "", return_type)).strip()
        if not re.fullmatch(r"(?:unsigned\s+|signed\s+)?(?:char|short|int|long(?:\s+long)?|float|double|size_t|_Bool|bool)", ret_base):
            raise InvalidFormatError(f"Kiểu mảng trả về C chưa được hỗ trợ: {return_type}")
        formatter = "%.17g" if ret_base in {"float", "double"} else "%lld"
        cast = "(double)" if ret_base in {"float", "double"} else "(long long)"
        output = f"{ret_base} *__result = {call}; putchar('['); for(int __i=0; __i<{return_size_name}; ++__i){{if(__i)putchar(','); printf(\"{formatter}\",{cast}__result[__i]);}} putchar(']');"
    elif ret_kind == "string":
        output = f"char *__result = {call}; qstr(__result ? __result : \"\");"
    elif ret_kind == "number":
        output = f"double __result = {call}; printf(\"%.17g\", __result);"
    elif ret_kind == "bool":
        output = f"int __result = {call}; fputs(__result ? \"true\" : \"false\", stdout);"
    elif ret_kind == "char":
        output = f"char __result = {call}; char __text[2]={{__result,0}}; qstr(__text);"
    elif ret_kind == "void":
        output = f"{call}; fputs(\"null\", stdout);"
    else:
        output = f"long long __result = (long long){call}; printf(\"%lld\", __result);"
    array_check = " || ".join(array_slot_checks)
    array_check = f" || __cham_input->n > {consumed}" + (f" || {array_check}" if array_check else "")
    driver = f'''\nint main(void) {{\n  size_t __cap=4096,__n=0; char *__buffer=(char*)malloc(__cap); int __ch; while((__ch=getchar())!=EOF){{if(__n+1>=__cap){{__cap*=2;__buffer=(char*)realloc(__buffer,__cap);}}__buffer[__n++]=(char)__ch;}} __buffer[__n]=0; cur=__buffer; J *__cham_input=parse();\n  if (__cham_input->type != 4 || __cham_input->n < {consumed}{array_check}) return 2;\n  {''.join(declarations)}\n  fputs("\\n@@CHAM_CODE_RESULT@@",stdout); {output} return 0;\n}}\n'''
    return _C_RUNTIME + "\n" + student_code + "\n" + driver

def _builds(language: str, code: str, function_name: str) -> str | None:
    """None nếu harness dựng được từ starter này, ngược lại trả lý do lỗi."""
    try:
        build_source(language, code, function_name, code)
    except InvalidFormatError as error:
        return error.message
    except (ValueError, TypeError) as error:
        return str(error)
    return None


def validate_starter_codes(function_name: str | None, starter_codes: dict[str, str]) -> None:
    if set(starter_codes) - set(ALL_STARTER_LANGUAGES) or any(
        not isinstance(code, str) for code in starter_codes.values()
    ):
        raise InvalidFormatError(
            "starter_codes chỉ nhận Python, C, C++, Java, JavaScript và giá trị phải là chuỗi"
        )
    if function_name is None:
        for language, code in list(starter_codes.items()):
            if not code.strip():
                starter_codes.pop(language)
        return
    if any(not code.strip() for code in starter_codes.values()):
        raise InvalidFormatError("starter_codes của bài function mode không được để trống")
    if "java" in starter_codes:
        raise InvalidFormatError("Bài chấm theo function_name không hỗ trợ starter code Java")
    missing = [lang for lang in REQUIRED_HARNESS_LANGUAGES if lang not in starter_codes]
    if missing:
        raise InvalidFormatError(
            f"Bài chấm theo function_name bắt buộc có starter code: {', '.join(missing)}"
        )
    for language in REQUIRED_HARNESS_LANGUAGES:
        if not re.search(rf"\b{re.escape(function_name)}\b", starter_codes[language]):
            raise InvalidFormatError(
                f"starter_codes.{language} phải chứa function_name '{function_name}'"
            )
    for language in OPTIONAL_HARNESS_LANGUAGES:
        if language in starter_codes:
            reason = _builds(language, starter_codes[language], function_name)
            if reason:
                raise InvalidFormatError(
                    f"starter_codes.{language} không dùng được với harness: {reason}. "
                    f"Sửa chữ ký hoặc bỏ starter {language} để bài chỉ hỗ trợ các ngôn ngữ còn lại"
                )


def prune_unsupported_starters(function_name: str, starter_codes: dict[str, str]) -> dict[str, str]:
    """Bỏ starter C/C++ mà harness không dựng được (dùng khi import hàng loạt)."""
    return {
        language: code
        for language, code in starter_codes.items()
        if language not in OPTIONAL_HARNESS_LANGUAGES
        or (isinstance(code, str) and _builds(language, code, function_name) is None)
    }


def starter_codes_of(problem) -> dict[str, str]:
    if problem.starter_codes:
        return problem.starter_codes
    legacy = (problem.start_format_code or "").strip()
    return {"python": problem.start_format_code} if legacy else {}


def supported_languages(problem) -> list[str]:
    if problem.function_name is None:
        return list(config.LANGUAGES)
    starters = starter_codes_of(problem)
    return [
        lang for lang in HARNESS_LANGUAGES
        if lang in config.LANGUAGES and starters.get(lang, "").strip()
    ]
