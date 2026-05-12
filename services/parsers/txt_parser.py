import re

class TestParserPipeline:
    """
    Ультра-гнучка архітектура парсингу тестів.
    Працює з ідеальними тестами та з "університетським сміттям" (без номерів, без літер).
    """
    def __init__(self):
        # Патерн маркерів варіантів: "А.", "Б)", "a)", "-", "+", "*", "1)"
        self.opt_marker_pattern = re.compile(r'^([А-Яа-яA-Za-zІіЇїЄє][\.\)]|[\-\+\*]|\d+[\)])\s+')
        
        # ВДОСКОНАЛЕНИЙ патерн номерів: ловить "1.", "145)", "10.1.", "10.1 "
        self.q_num_pattern = re.compile(r'^\s*(?:\d+\.\d+(?:\.\d+)*[\.\)]?|\d+[\.\)])\s+')
        
        # Патерн для очищення варіантів (ловить "+А. ", "- Б)" тощо)
        self.clean_opt_pattern = re.compile(r'^(\+?[А-Яа-яA-Za-zІіЇїЄє][\.\)]|[\-\+\*]|\d+[\)])\s*')

    def parse(self, raw_text: str, options_count: int = None) -> list:
        clean_text = self._sanitize(raw_text)

        # СЦЕНАРІЙ 1: Користувач вказав точну кількість варіантів
        if options_count and options_count > 0:
            results_fixed = self._strategy_fixed_options(clean_text, options_count)
            if len(results_fixed) > 0:
                return self._validate_and_clean(results_fixed)

        # СЦЕНАРІЙ 2: Автоматичне розпізнавання (якщо підказки немає)
        results_heuristic = self._strategy_heuristic(clean_text)
        results_blocks = self._strategy_blocks(clean_text)

        best_results = self._evaluate_results([results_heuristic, results_blocks])
        return self._validate_and_clean(best_results)

    def _sanitize(self, text: str) -> str:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\uf0b7]', '', text)
        text = text.replace('•', '').replace('', '')
        # Залишаємо максимум два перенесення рядка підряд (для блоків)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def _strategy_fixed_options(self, text: str, n: int) -> list:
        """
        ІДЕАЛЬНА СТРАТЕГІЯ ЗА ПІДКАЗКОЮ. 
        Розбиває текст на блоки. Якщо текст зліплений - використовує математичний поділ.
        """
        questions = []
        raw_blocks = re.split(r'\n\s*\n', text)
        
        blocks = []
        for raw_block in raw_blocks:
            lines = [line.strip() for line in raw_block.split('\n') if line.strip()]
            if not lines: continue
            
            # КРОК А: Спроба розбити по номерах (якщо вони є)
            subblocks = []
            curr = []
            has_numbers = False
            for line in lines:
                if self.q_num_pattern.match(line):
                    has_numbers = True
                    if curr: subblocks.append(curr)
                    curr = [line]
                else:
                    curr.append(line)
            if curr: subblocks.append(curr)
            
            if has_numbers and len(subblocks) > 1:
                blocks.extend(subblocks)
                continue
                
            # КРОК Б: Математичний поділ (якщо текст зліплений і немає номерів)
            # Якщо розмір блоку більше ніж 2 питання, перевіряємо, чи ділиться він ідеально
            if len(lines) >= (n + 1) * 2:
                if len(lines) % (n + 1) == 0:
                    for i in range(0, len(lines), n + 1):
                        blocks.append(lines[i : i + n + 1])
                    continue
            
            # Якщо нічого не допомогло (або це вже ідеальний блок, відділений пустим рядком)
            blocks.append(lines)

        # Тепер формуємо фінальні питання з готових блоків
        for block_lines in blocks:
            if len(block_lines) > n:
                q_text = " ".join(block_lines[:-n]) # Все крім останніх N рядків - питання
                opts = block_lines[-n:]             # Останні N рядків - варіанти
                
                final_opts = []
                correct_opt = None
                
                for opt in opts:
                    # Відрізаємо літери та символи
                    clean_opt = self.clean_opt_pattern.sub('', opt).strip()
                    
                    if opt.startswith('+'):
                        clean_opt = re.sub(r'^\+\s*', '', clean_opt) 
                        correct_opt = clean_opt
                    else:
                        final_opts.append(clean_opt)
                        
                if correct_opt:
                    final_opts.insert(0, correct_opt)
                    
                questions.append({
                    "content": q_text,
                    "options": final_opts
                })
                
        return questions

    def _strategy_heuristic(self, text: str) -> list:
        questions = []
        curr_q = []
        curr_opts = []
        lines = [line.strip() for line in text.split('\n')]

        for line in lines:
            if not line: continue
            opt_match = self.opt_marker_pattern.match(line)
            is_opt_marker = bool(opt_match)
            is_q_marker = bool(self.q_num_pattern.match(line))
            is_new_q = False

            if curr_opts:
                if is_q_marker: is_new_q = True
                elif len(curr_opts) >= 2 and line.endswith('?'): is_new_q = True
                elif len(curr_opts) >= 3 and re.match(r'^[А-ЯІЇЄA-Z]', line) and not is_opt_marker: is_new_q = True

            if is_new_q:
                questions.append({"content": " ".join(curr_q), "options": curr_opts})
                curr_q = [line]
                curr_opts = []
            else:
                if is_opt_marker:
                    clean_opt = line[opt_match.end():].strip()
                    marker_text = opt_match.group(1)
                    if '+' in marker_text: curr_opts.insert(0, clean_opt)
                    else: curr_opts.append(clean_opt)
                elif curr_opts: curr_opts.append(line)
                elif curr_q:
                    if curr_q[-1].endswith('?') or curr_q[-1].endswith(':'): curr_opts.append(line)
                    else:
                        if len(line) < 150 and re.match(r'^[-+*а-яієїa-z]', line): curr_opts.append(line)
                        else: curr_q.append(line)
                else: curr_q.append(line)

        if curr_q and len(curr_opts) >= 2:
            questions.append({"content": " ".join(curr_q), "options": curr_opts})
        return questions

    def _strategy_blocks(self, text: str) -> list:
        questions = []
        blocks = re.split(r'\n\s*\n', text)
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if len(lines) >= 3:
                opt_start_idx = 1
                for i in range(1, len(lines)):
                    if self.opt_marker_pattern.match(lines[i]) or lines[i-1].endswith('?'):
                        opt_start_idx = i
                        break
                if opt_start_idx == 1 and not lines[0].endswith('?'):
                    opt_start_idx = max(1, len(lines) - 5)

                q_text = " ".join(lines[:opt_start_idx])
                opts = lines[opt_start_idx:]
                final_opts = []
                for opt in opts:
                    clean_o = self.clean_opt_pattern.sub('', opt).strip()
                    if opt.startswith('+'): final_opts.insert(0, clean_o)
                    else: final_opts.append(clean_o)
                        
                if len(final_opts) >= 2:
                    questions.append({"content": q_text, "options": final_opts})
        return questions

    def _evaluate_results(self, results_list: list) -> list:
        best_result = []
        best_score = -1
        for res in results_list:
            if not res: continue
            num_q = len(res)
            opt_counts = [len(q['options']) for q in res]
            avg_opts = sum(opt_counts) / num_q if num_q else 0
            score = num_q if 2 <= avg_opts <= 6 else num_q * 0.5
            if score > best_score:
                best_score = score
                best_result = res
        return best_result

    def _validate_and_clean(self, questions: list) -> list:
        valid_questions = []
        for q in questions:
            content = re.sub(r'^\s*(?:\d+\.\d+(?:\.\d+)*[\.\)]?|\d+[\.\)])\s*', '', q["content"]).strip()
            if not content: content = "Питання без тексту"

            clean_opts = []
            for opt in q["options"]:
                o = self.clean_opt_pattern.sub('', opt).strip()
                if o: clean_opts.append(o)

            if len(clean_opts) >= 2:
                valid_questions.append({
                    "content": content,
                    "options": clean_opts,
                    "correct_answer": clean_opts[0] 
                })
        return valid_questions

def parse_txt_content(content: str, options_count: int = None) -> list:
    pipeline = TestParserPipeline()
    return pipeline.parse(content, options_count)