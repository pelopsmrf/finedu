import { describe, expect, test } from "vitest";
import { scoreQuiz } from "./quizLogic";

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
