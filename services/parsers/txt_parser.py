import re

class TestParserPipeline:
    """
    Багатоступенева архітектура парсингу тестів.
    Конвеєр: Очищення -> Сувора стратегія -> Гнучка стратегія (резерв) -> Валідація
    """
    def __init__(self):
        # Ловить варіанти: "А.", "Б)", "a." ігноруючи сміття зліва
        self.opt_pattern = re.compile(r'^[^a-zA-Zа-яА-ЯІіЇїЄє0-9]*([A-Za-zА-Яа-яІіЇїЄє])[\.\)]\s*(.*)')
        # Ловить номери: "1.", "1471)", "2 " на початку рядка
        self.num_pattern = re.compile(r'(?m)^\s*\d+[\.\)]?\s+')

    def parse(self, raw_text: str) -> list:
        """Оркестратор процесу парсингу"""
        # Етап 1: Очищення
        clean_text = self._sanitize(raw_text)

        # Етап 2: Спроба розбити суворим методом
        results = self._strategy_strict(clean_text)

        # Етап 3: Якщо суворий метод знайшов замало тестів, вмикаємо гнучкий автомат станів
        if len(results) < 5:
            results = self._strategy_flexible(clean_text)

        # Етап 4: Фінальна валідація та форматування
        return self._validate_and_clean(results)

    def _sanitize(self, text: str) -> str:
        """Видаляє невидимі символи та артефакти OCR/PDF."""
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\uf0b7]', '', text)
        text = text.replace('•', '').replace('', '')
        return text

    def _strategy_strict(self, text: str) -> list:
        """Блоковий парсинг: розрізає текст по номерах питань."""
        blocks = self.num_pattern.split(text)
        blocks = [b.strip() for b in blocks if b.strip()]

        questions = []
        for block in blocks:
            parsed_q = self._parse_single_block(block)
            if parsed_q:
                questions.append(parsed_q)
        return questions

    def _strategy_flexible(self, text: str) -> list:
        """
        Автомат станів (State Machine): рядок за рядком.
        Перемикає стан на 'нове питання', коли після варіантів відповідей знову йде текст.
        """
        questions = []
        current_q_text = []
        current_options = []

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for line in lines:
            match = self.opt_pattern.match(line)

            if match:
                # Стан: Збір варіантів відповідей. Беремо тільки текст, без літери.
                opt_text = match.group(2).strip()
                current_options.append(opt_text)
            else:
                # Стан: Збір тексту питання
                if current_options:
                    # Якщо ми натрапили на текст, але вже маємо опції — це початок НОВОГО питання
                    if len(current_options) >= 2:
                        questions.append({
                            "content": " ".join(current_q_text),
                            "options": current_options
                        })
                    
                    # Скидаємо буфери для нового циклу
                    current_q_text = [line]
                    current_options = []
                else:
                    # Якщо опцій ще не було, просто дописуємо текст до поточного питання
                    current_q_text.append(line)

        # Зберігаємо "хвіст"
        if current_q_text and len(current_options) >= 2:
            questions.append({
                "content": " ".join(current_q_text),
                "options": current_options
            })

        return questions

    def _parse_single_block(self, block_text: str) -> dict:
        """Внутрішній метод суворої стратегії для обробки одного розрізаного блоку."""
        lines = block_text.split('\n')
        q_text_lines = []
        options = []

        for line in lines:
            line = line.strip()
            if not line: continue

            match = self.opt_pattern.match(line)
            if match:
                # Зберігаємо тільки текст варіанту
                opt_text = match.group(2).strip()
                options.append(opt_text)
            else:
                if not options:
                    q_text_lines.append(line)
                else:
                    # Якщо текст іде після початку опцій, склеюємо його з останньою опцією
                    options[-1] += " " + line

        if q_text_lines and len(options) >= 2:
            return {
                "content": " ".join(q_text_lines),
                "options": options
            }
        return None

    def _validate_and_clean(self, questions: list) -> list:
        """Остаточне "причісування" даних перед відправкою у БД."""
        valid_questions = []

        for q in questions:
            content = q["content"].strip()
            
            # Відрізаємо номери питань, які могли "прилипнути" на початку (напр. "1471 Яке око...")
            content = re.sub(r'^[^A-Za-zА-Яа-яІіЇїЄє]*\d+[\.\)]?\s*', '', content).strip()

            if not content:
                content = "Питання без тексту"

            valid_questions.append({
                "content": content,
                "options": q["options"],
                "correct_answer": q["options"][0]  # За замовчуванням правильна відповідь — перша (тепер вона теж без літери)
            })

        return valid_questions

# Точка входу для FastAPI роутера
def parse_txt_content(content: str) -> list:
    pipeline = TestParserPipeline()
    return pipeline.parse(content)