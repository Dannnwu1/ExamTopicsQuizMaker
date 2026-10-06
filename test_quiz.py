import unittest

from _classes import CardList


class CardListParsingTests(unittest.TestCase):
    def test_reads_single_answer_correctly(self):
        cards = CardList("./res").cards_list
        self.assertTrue(cards)
        self.assertEqual(cards[0].correct_answer, "A")

    def test_reads_multiple_choice_answers(self):
        cards = CardList("./res").cards_list
        multi_answer_values = {card.correct_answer for card in cards if len(card.correct_answer) > 1}
        self.assertIn("ADF", multi_answer_values)


if __name__ == "__main__":
    unittest.main()
