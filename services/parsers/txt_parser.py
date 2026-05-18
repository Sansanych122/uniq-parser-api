import re

class TestParserPipeline:
    """
    Мульти-ядерна архітектура парсингу. 
    Одночасно застосовує 4 різні стратегії для аналізу тексту і 
    використовує Суддю (Scoring System), щоб обрати найякісніший результат.
    """
    def __init__(self):
        # Патерн, що ловить маркери: "А. ", "Б) ", "a)", "-", "+", "*", "1) "
        self.OPT_MARKER = re.compile(r'^\s*(?:(?:[\+\-\*]\s*)?(?:[А-Яа-яA-Za-zІіЇїЄєҐґ][\.\)]|\d+[\)])\s+|[\+\-\*](?=\s|[А-Яа-яA-Za-zІіЇїЄєҐґ]))')
        
        # Патерн для видалення нумерації: "1.", "145)", "10.1.1. ", "1 "
        self.Q_NUM = re.compile(r'^\s*(?:\d+(?:[\.\)]\s*\d+)*[\.\)]?|\d+\s+(?=[A-ZА-ЯІЇЄҐ3"\'«]))\s*')
        
        # Патерн для очищення варіантів перед збереженням у БД
        self.CLEAN_OPT = re.compile(r'^\s*(?:(?:[\+\-\*]\s*)?(?:[А-Яа-яA-Za-zІіЇїЄєҐґ][\.\)]|\d+[\.\)])|[\+\-\*]\s*)\s*')

    def parse(self, raw_text: str, options_count: int = None) -> list:
        clean_text = self._sanitize(raw_text)
        
        # ЗАПУСК 4-х АЛГОРИТМІВ ПАРАЛЕЛЬНО
        res1 = self._strategy_blank_lines(clean_text, options_count)
        res2 = self._strategy_numbers(clean_text, options_count)
        res3 = self._strategy_monolith(clean_text, options_count)
        res4 = self._strategy_markers(clean_text, options_count)
        
        # СУДДЯ ВИБИРАЄ НАЙКРАЩИЙ РЕЗУЛЬТАТ
        best_results = self._evaluate([res1, res2, res3, res4], options_count)
        
        return self._validate_and_clean(best_results)

    def _sanitize(self, text: str) -> str:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\uf0b7]', '', text)
        text = text.replace('•', '').replace('', '')
        # Видалення колонтитулів (наприклад "--- PAGE 12 ---")
        text = re.sub(r'(?i)\n*-*\s*(?:page|стор\.?|сторінка)\s*\d+\s*-*\n*', '\n\n', text)
        text = re.sub(r'\n\s*\d+\s*\n', '\n\n', text) 
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    # =========================================================
    # СТРАТЕГІЯ 1: Ідеальні блоки
    # =========================================================
    def _strategy_blank_lines(self, text: str, n: int) -> list:
        blocks = re.split(r'\n\s*\n', text)
        return [q for q in (self._extract_q_opts(b.split('\n'), n) for b in blocks if b.strip()) if q]

    # =========================================================
    # СТРАТЕГІЯ 2: Орієнтація на номери
    # =========================================================
    def _strategy_numbers(self, text: str, n: int) -> list:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        chunks, curr = [], []
        
        for line in lines:
            # Якщо це номер питання (і не випадкове "1)" всередині варіантів)
            is_q_num = self.Q_NUM.match(line)
            is_fake_num = curr and re.match(r'^\s*\d+\)', line) and self.OPT_MARKER.match(line)
            
            if is_q_num and not is_fake_num:
                if curr: chunks.append(curr)
                curr = [line]
            else:
                curr.append(line)
                
        if curr: chunks.append(curr)
        return [q for q in (self._extract_q_opts(c, n) for c in chunks) if q]

    # =========================================================
    # СТРАТЕГІЯ 3: Орієнтація на маркери відповідей А.Б.В.
    # =========================================================
    def _strategy_markers(self, text: str, n: int) -> list:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        chunks, curr = [], []
        in_opts = False
        
        for line in lines:
            if self.OPT_MARKER.match(line):
                in_opts = True
                curr.append(line)
            else:
                # Якщо ми у варіантах, і рядок починається не з малої літери -> це нове питання
                if in_opts and not re.match(r'^\s*[а-яієїґa-z]', line):
                    if curr: chunks.append(curr)
                    curr = [line]
                    in_opts = False
                else:
                    curr.append(line)
                    
        if curr: chunks.append(curr)
        return [q for q in (self._extract_q_opts(c, n) for c in chunks) if q]

    # =========================================================
    # СТРАТЕГІЯ 4: "Суцільна каша" 
    # =========================================================
    def _strategy_monolith(self, text: str, n: int) -> list:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        chunks, curr = [], []
        opts_gathered = 0
        in_opts = False
        
        has_global_markers = sum(1 for l in lines if self.OPT_MARKER.match(l)) > 5
        
        for line in lines:
            is_new_q = False
            
            if in_opts:
                is_opt = self.OPT_MARKER.match(line) if has_global_markers else re.match(r'^\s*[\+\-\*А-ЯІЇЄҐA-Z0-9]', line)
                if is_opt: opts_gathered += 1
                
                # Жорстке відрізання
                if n and opts_gathered > int(n):
                    is_new_q = True
                elif not n and opts_gathered > 1:
                    if line.endswith('?'):
                        is_new_q = True
                    elif len(line) > 60 and line[0].isupper() and not self.OPT_MARKER.match(line):
                        if curr and len(curr[-1]) < 60:
                            is_new_q = True
                            
            if not in_opts and (line.endswith('?') or line.endswith(':')):
                in_opts = True
                opts_gathered = 0
                
            if is_new_q:
                if curr: chunks.append(curr)
                curr = [line]
                in_opts = False
                opts_gathered = 0
                if line.endswith('?'): in_opts = True
            else:
                curr.append(line)
                
        if curr: chunks.append(curr)
        return [q for q in (self._extract_q_opts(c, n) for c in chunks) if q]

    # =========================================================
    # УНІВЕРСАЛЬНИЙ РОЗБИВАЧ (Питання + Склеювання Варіантів)
    # =========================================================
    def _extract_q_opts(self, lines: list, n: int) -> dict:
        if len(lines) < 2: return None
        lines = [l for l in lines if l.strip()]
        
        opt_start = -1
        # 1. Пошук першого А. Б. В.
        for i, l in enumerate(lines):
            if i > 0 and self.OPT_MARKER.match(l):
                opt_start = i
                break
                
        # 2. Пошук знаку питання
        if opt_start == -1:
            for i, l in enumerate(lines):
                if l.endswith('?') or l.endswith(':'):
                    opt_start = i + 1
                    break
                    
        # 3. Примусове розбиття
        if opt_start == -1 or opt_start >= len(lines):
            if n and len(lines) > int(n):
                opt_start = len(lines) - int(n)
            else:
                opt_start = 1
                
        q_text = " ".join(lines[:opt_start])
        opts_raw = lines[opt_start:]
        if not opts_raw: return None
        
        # ІНТЕЛЕКТУАЛЬНЕ СКЛЕЮВАННЯ БАГАТОРЯДКОВИХ ВАРІАНТІВ
        options = []
        curr_opt = []
        
        # Перевірка: чи всі варіанти мають А. Б.? Якщо так, довіряємо лише маркерам
        strict_markers = sum(1 for o in opts_raw if self.OPT_MARKER.match(o))
        trust_markers_only = strict_markers >= len(opts_raw) - 1
        
        for o in opts_raw:
            is_marker = bool(self.OPT_MARKER.match(o))
            is_logical = bool(re.match(r'^\s*[\+\-\*А-ЯІЇЄҐA-Z0-9]', o))
            
            is_new = is_marker if trust_markers_only else (is_marker or is_logical)
                
            if is_new and curr_opt:
                options.append(" ".join(curr_opt))
                curr_opt = [o]
            else:
                curr_opt.append(o)
                
        if curr_opt: options.append(" ".join(curr_opt))
        return {"content": q_text, "options": options}

    # =========================================================
    # СУДДЯ
    # =========================================================
    def _evaluate(self, strategies_results: list, hint_n: int) -> list:
        best_res = []
        best_score = -float('inf')

        for res in strategies_results:
            if not res: continue
            score = 0
            num_q = len(res)
            if num_q < 2: continue
            
            score += num_q * 100 # Бонус за кількість знайдених тестів
            
            for q in res:
                num_opts = len(q['options'])
                
                # Жорсткі штрафи за "зліплені" тести
                if num_opts < 2: score -= 300
                elif num_opts > 8: score -= 50
                
                # Нагорода за підказку
                if hint_n and num_opts == int(hint_n): score += 50
                elif not hint_n and 3 <= num_opts <= 6: score += 20
                
                content = q['content'].strip()
                if content.endswith('?'): score += 30
                if len(content) < 15: score -= 50
                
            if score > best_score:
                best_score = score
                best_res = res

        return best_res

    def _validate_and_clean(self, questions: list) -> list:
        valid = []
        for q in questions:
            # Ідеальне зачищення номерів (видаляє навіть 10.1.1.)
            content = self.Q_NUM.sub('', q["content"]).strip()
            content = re.sub(r'^\s*(?:\d+[\.\)]\s*)+', '', content).strip()
            if not content: content = "Питання без тексту"

            clean_opts = []
            correct_opt = None

            for opt in q["options"]:
                is_correct = opt.strip().startswith('+')
                clean_o = self.CLEAN_OPT.sub('', opt).strip()
                clean_o = re.sub(r'^\+\s*', '', clean_o).strip()

                if is_correct: correct_opt = clean_o
                if clean_o: clean_opts.append(clean_o)

            # Формування бази для БД
            if correct_opt and correct_opt in clean_opts:
                clean_opts.remove(correct_opt)
                clean_opts.insert(0, correct_opt)
            elif correct_opt:
                clean_opts.insert(0, correct_opt)

            if len(clean_opts) >= 2:
                valid.append({
                    "content": content,
                    "options": clean_opts,
                    "correct_answer": clean_opts[0]
                })
        return valid

def parse_txt_content(content: str, options_count: int = None) -> list:
    pipeline = TestParserPipeline()
    return pipeline.parse(content, options_count)