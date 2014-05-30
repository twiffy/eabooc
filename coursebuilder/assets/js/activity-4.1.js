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

  '<table border="2"><tr><td><b>Note:</b><p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.<p></td></tr></table><br>',

  '<h1>Unit 4 (Chapter 8 and 9) Practice Test</h1>',

  'While you were able to choose to highlight and discuss just one type of assessment in Unit 4, <b>for the final exam you are responsible for the material in both Chapter 8</b> (performance assessment) <b>and Chapter 9</b> (portfolio assessment).',

  "<h2>Part 1 - Performance Assessment</h2>",

  "<p>Please read the following fictional vignette describing Mr. Caldwell’s use of performance assessment in his classroom.  Based on the material contained in Chapter 8 (Performance Assessment), you will find that the teacher made a number of mistakes.  After reading the vignette, please briefly identify <b>three</b> of the four blatant mistake(s) the teacher made in employing classroom-level performance assessment.",

  "<blockquote>Mr. Caldwell teaches social studies classes in an inner-city high school.  As part of a masters degree program he is completing at a nearby university, Mr. Caldwell took a course last year in classroom assessment (and earned an A).  This year, he is attempting to incorporate some of the things he learned in this assessment class.  In particular, he is trying to apply to his geography course what he has learned about performance testing.</blockquote>",

  "<blockquote>Because the district’s content standards for tenth-grade geography focus on 18 fairly specific skills, Mr. Caldwell uses a performance testing approach to measure students’ mastery of each of those 18 geographic skills.  Therefore, he tries to use a new performance test almost every week during the single semester when he teaches the geography course.  Typically, students take a performance test on the last day of the week, and receive their graded responses back from Mr. Caldwell on the following Monday.</blockquote>",

  "<blockquote>Mr. Caldwell believes students’ self-evaluation of their own geographic skills is crucial to their achievement.  For each performance test, therefore, he develops a detailed rubric for them (and him) to use in judging their performances.  He distributes this rubric to students at the beginning of instruction regarding each of the 18 skills.  For each of the 18 skills, Mr. Caldwell has identified a minimum of 10 and a maximum of 15 evaluative criteria which, largely because of fairly clear labels, students seem to understand rather well.  For example, in a performance test dealing with Map Usage, one of the evaluative criteria is “Suitable Map-Type Chosen.”</blockquote>",

  "<blockquote>Then, for each of these labeled evaluative criteria, Mr. Caldwell assigns one-to-five points for each student’s response.  More points are better than fewer points.  Mr. Caldwell indicates that the point allocations should roughly match an <i>A</i>-through-<i>F</i> grading system.</blockquote>",

  "<blockquote>Although his weekends are busy, Mr. Caldwell grades each student’s responses to that week’s performance test using, first, a holistic scoring approach and, thereafter, an analytic scoring approach.</blockquote>",

  "<blockquote>Although he is often exhausted by his implementation of performance assessment, Mr. Caldwell is convinced the instructional dividends his students derive from this measurement approach make it well worthwhile.  (And, of course, he wants to show that the <i>A</i> he earned in his classroom assessment course has paid off!)</blockquote>",

  "<p>List three of Mr. Caldwell's mistakes:</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "There are four fairly blatant mistakes Mr. Caldwell made in carrying out performance assessment in his class.\n\nFirst, he did too much of it, making almost certain he’ll not long continue to employ this assessment approach.\n\nSecond, he used too many evaluative criteria.\n\nThird, he never described levels of quality from students’ responses, only assigning mystery numbers based on A-through-F grades.\n\nFinally, he applied both holistic and analytic scoring to every response—an injudicious use of his time.  Mr. Caldwell, as is often true with the recently converted, is far too zealous about performance testing.",
    correctAnswerOutput: "bug",
    outputHeight: "220px"

  },


  "<h2>Part 2 - Portfolio Assessment</h2>",

  "<p>Three of the following five statements are false. Identify the three false items and rewrite those statements to make them true.</p>",

  '<h3>Statement 1</h3>',
  '<blockquote>Fortunately, well organized instructors do not need to devote much time to the conduct of portfolio conferences.</blockquote>',
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The statement is false.  Portfolio conferences take time. Instructors should take time prior to the conference to prepare so that the instructor can make the conference itself time efficient, focusing on the topics of most concern to the instructor and student.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 2</h3>",
  "<blockquote>When held, portfolio conferences should not only deal with the evaluation of a student’s work products, but should also improve the student’s self-evaluation abilities.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This statement is true.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 3</h3>",
  "<blockquote>In order for students to evaluate their own efforts, the evaluative criteria to be used in judging a portfolio’s work products must be identified, then made known to students.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This statement is true.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 4</h3>",
  "<blockquote>Students should rarely be involved in the determination of the evaluative criteria by which a portfolio’s products will be appraised.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The statement is false.  The instructor should work collaboratively with the students to determine the evaluative criteria by which a portfolio’s products will be appraised.",
    correctAnswerOutput: "bug"
  },


  "<h3>Statement 5</h3>",
  "<blockquote>Students should be asked to review their own work products only near the end of the course so their self-evaluations can be more accurate.</blockquote>",
  "True or false?  If false, your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The statement is false.  Students should be asked to review their own work throughout the course, not only at the end of the course. That is, self-evaluation should be a routine part of the course.",
    correctAnswerOutput: "bug"
  },

];

