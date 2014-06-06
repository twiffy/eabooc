// Copyright 2012 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


// Usage instructions: Create a single array variable named 'activity'. This
// represents explanatory text and one or more questions to present to the
// student. Each element in the array should itself be either
//
// -- a string containing a set of complete HTML elements. That is, if the
//    string contains an open HTML tag (such as <form>), it must also have the
//    corresponding close tag (such as </form>). You put the actual question
//    text in a string.
//
// -- a JavaScript object representing the answer information for a question.
//    That is, the object contains properties such as the type of question, a
//    regular expression indicating the correct answer, a string to show in
//    case of either correct or incorrect answers or to show when the student
//    asks for help. For more information on how to specify the object, please
//    see http://code.google.com/p/course-builder/wiki/CreateActivities.

//
// This is not "real" javascript.  The Python code must be able to parse it,
// and gives parse errors (not semantic errors) if you (e.g.) use different
// fields than it expects.
//

var activity = [

  '<p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.</p>',

  '<h1>Unit 5 (Chapter 3 and 5) Practice Test</h1>',

  '<p>This practice test covers two chapters; there are three questions per chapter.</p>',

  '<h2>Part 1 - Reliability</h2>',

  '<p>For these items, you should read the scenario and choose the type of reliability evidence that is the best choice: Stability, Alternate Forms, or Internal Consistency. Then briefly explain why that is the best choice.',

  "<p><b>1.1</b> - A school district’s testing office has been directed to construct a basic skills test in language arts that can be taken at any point during an extensive three-month summer session by eighth-grade students who failed an earlier test.  By district policy, the earlier test must be passed before students can enroll in the ninth grade.  The school board’s policy, however, says that the student can choose the occasion (one time per student) when an alternate test is administered.  Critics of the policy fear there will be striking differences in students’ performances depending on when they choose to be tested with the alternate test.  What kind of reliability evidence seems most needed in this setting, and why?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Stability evidence.\n\nThis is a tough choice because the board’s policy is so bizarre. Stability is the best choice because what is hoped to be achieved is a test-retest stability between two administrations of a single test. However, a case could be made for alternate-forms evidence because students are allowed to choose an alternative test (one time per student).",
    correctAnswerOutput: "bug",
    outputHeight: "100px"

  },



  "<p><b>1.2</b> - A Texas school superintendent in a district near the Mexican border has asked his assessment specialist, Mr. Chavez, to create a brief test that will provide the district’s educators with a general idea of immigrant students’ ability to read English.  Mr. Chavez builds a 20-item test, administered with the use of audiotaped directions in Spanish.  All of the items, however, are written in English.  The test’s overall function is to yield a single estimate of a Spanish-speaking student’s ability to read English.  What kind of reliability evidence would be most informative in this situation, and why?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Internal Consistency evidence.\n\nThis type of consistency is concerned with the way the items function on the exam. Here the concern is about how the written items function similarly within the exam.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  "<p><b>1.3</b> - Based on a new state law, high-school students are going to be permitted to take a basic skills graduation test, administered via a computer, at any time during a three-week test-administration window.  Only one version of the test will be available each year, for the test will be substantially revised the following year.  What kind of reliability evidence seems most needed here for each year’s test, and why?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Stability evidence.\n\nThere is just one version of the exam being administered; therefore, the best test of reliability would be to collect stability (test-retest) evidence.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },

  "<h2>Part 2 - Bias</h2>",

  "<p>For the following four items, decide whether the item is true or false. If the item is false, rewrite the item to be true.</p>",

  '<h3>Statement 1</h3>',
  '<blockquote>Even if the individual items in a test are judged to be bias-free, it is possible for the total set of items, in aggregate, to be biased.</blockquote>',
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "No rewrite needed.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 2</h3>",
  "<blockquote>Typically, judgment-only approaches to the detection of item bias are employed prior to use of empirical bias-detection techniques.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "No rewrite needed.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 3</h3>",
  "<blockquote>If a teacher’s classroom test in mathematics deals with content more likely to be familiar to girls than boys, it is likely the test may be biased.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "No rewrite needed.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 4</h3>",
  "<blockquote>Empirical bias-detection techniques, especially DIF-biased approaches, will invariably identify more biased items than will even a well-trained and representative bias-review committee.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Empirical bias-detection techniques, especially DIF-biased approaches, will not necessarily identify more biased items than a well-trained and representative bias-review committee. This is because large numbers of students are required for empirical-bias reduction approaches to work.",
    correctAnswerOutput: "bug"
  },


];

