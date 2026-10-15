import { describe, expect, test } from "vitest";
import { pluralRu, resultMessage, scoreQuiz } from "./quizLogic";

describe("scoreQuiz", () => {
  test("scores correct and incorrect answers", () => {
    const questions = [{ correct_index: 0 }, { correct_index: 1 }];
    expect(scoreQuiz(questions, [0, 1])).toEqual({ score: 2, total: 2 });
    expect(scoreQuiz(questions, [1, 1])).toEqual({ score: 1, total: 2 });
  });

  test("handles missing answers as incorrect", () => {
    const questions = [{ correct_index: 0 }, { correct_index: 1 }];
    expect(scoreQuiz(questions, [0])).toEqual({ score: 1, total: 2 });
  });
});

describe("resultMessage", () => {
  test("praises a perfect score", () => {
    expect(resultMessage(3, 3)).toContain("Отлично");
  });

  test("encourages a low score", () => {
    expect(resultMessage(0, 3)).toContain("повторить");
  });

  test("is empty for an empty quiz", () => {
    expect(resultMessage(0, 0)).toBe("");
  });
});

describe("pluralRu", () => {
  const forms: [string, string, string] = ["вопрос", "вопроса", "вопросов"];
  test.each([
    [1, "вопрос"],
    [3, "вопроса"],
    [5, "вопросов"],
    [11, "вопросов"],
    [12, "вопросов"],
    [21, "вопрос"],
    [22, "вопроса"],
  ])("%i → %s", (n, expected) => {
    expect(pluralRu(n, forms)).toBe(expected);
  });
});
