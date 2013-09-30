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


// When the assessment page loads, activity-generic.js will render the contents
// of the 'assessment' variable into the enclosing HTML webpage.

// For information on modifying this page, see
// https://code.google.com/p/course-builder/wiki/CreateAssessments.


var assessment = {
  // HTML to display at the start of the page
  preamble: '',

  // An ordered list of questions, with each question's type implicitly determined by the fields it possesses:
  //   choices              - multiple choice question (with exactly one correct answer)
  //   correctAnswerString  - case-insensitive string match
  //   correctAnswerRegex   - freetext regular expression match
  //   correctAnswerNumeric - freetext numeric match
  questionsList: [

    {questionHTML: 'Which of the following statements represents the significant difference between a “content standard” and a “performance standard”?',
      choices: [
        'The content standard represents what educators what students to do and the performance standard represents what educators want students to learn.',
        'The performance standard represents the academic knowledge and the content standards represent the achieved proficiency.',
        'The content standard represents the measurable skills and the performance standards represents behaviors that can be described only.',
        correct('The content standard represents what educators want students to learn academically and the performance standard represents the desired level of proficiency educators want to students to achieve.'),],

    },

	 

    {questionHTML: 'Which of the following is NOT a What-to-Assess Consideration?',
     choices: ['One useful point of advice for what to assess could come from your colleagues.',
               'A useful framework for assessment can be a few key curricular aims.',
               correct('You can mirror your classroom assessments on the assessments for state content standards.'),
               'You can do an analysis of the psychomotor, cognitive, and affective behaviors you want to focus on.',
               ],
     },
	 
	    {questionHTML: 'Which of the following statements is true:',
     choices: [
       'Curriculum is the <i>means</i> teachers employ to promote student achievement and instruction is the sought-for <i>ends</i> of instruction.',
       correct('Instruction is the <i>means</i> teachers employ to promote student achievement and curriculum is the sought-for <i>ends</i> of instruction.'), ],
     },	 
	 
    {questionHTML: 'Which of the following is NOT part of the General Item-Writing Guidelines?',
     choices: ['Check your items for unintentional cues that easily direct students to the correct responses.',
               'Use vocabulary familiar to your students because difficult vocabulary could make the items too confusing.',
               correct('Write perplexing directions to direct test takers into choosing an incorrect response.'),
               'Write items using simple sentence structure so not to unintentionally confuse your students.',],
     },	

	 
    {questionHTML: 'Which of the following is the greatest weakness of binary items?',
     choices: [
       correct('Students have a 50-50 chance of guessing the correct answer.'),
       'They are time-consuming assessments.',
       'It is impossible to cover a large amount of material.',
       'There is only one type of binary-choice item: true or false items.',
               ],
     },	 
   
	 
    {questionHTML: 'Multiple Binary-Choice Items are considered good test items for a number of reasons. Which of the following reasons is true for Multiple Binary-Choice Items?',
     choices: [
       'They are slightly easier than multiple-choice items.',
       'They are more valid than other selected-response items.',
       correct('They help instructors efficiently gather information on student achievement.'),
       'They are the easiest type of selected-response item to write.'
               ],
     },	 
   
	 
    {questionHTML: 'Which of the following presents the three parts of a Multiple-Choice Item according to Popham?',
     choices: [
       'Question, correct responses, and incorrect responses.',
       correct('Stem, item alternatives, and distractors.'),
       'Question, correct responses, and distractors.',
       'None-of-the-above.',
               ],
     },	 
   
	 
    {questionHTML: 'Which of the following is a disadvantage of Matching Items?',
     choices: [
       correct('They encourage memorization of low-level factual information.'),
       'They can be scored easily by holding a test key next to the responses.',
       'They do not take up much room on the test page.',
       'They allow for a lot of information to be tested quickly.',

               ],
     },	 
   
	 
    {questionHTML: 'Which of the following statements could be considered an advantage of Short-Answer Items?',
     choices: [
       'Issues of reliability may occur due to the possibility of inaccurate scoring.',
       'Longer responses lead to difficulties in scoring.',
       'Scoring short-answer items is fairly problematic.',
       correct('Longer responses lead to more optimal measurement of learning outcomes.'),
               ],
     },	 
   
	 
    {questionHTML: 'True or false. Essay items should elicit extended responses where students have complete freedom to determine how much to write.',
     choices: [
       'True',
       correct('False'),
               ],
     },	 
   
	 
    {questionHTML: '<em>For the next three questions, determine whether or not the statement is Accurate or Inaccurate. A statement’s accuracy depends on whether it represents a verbatim or appropriately paraphrased rendition of statements drawn from Chapter 7.</em><br>To best assess students’ ability to respond to essay items, allow students to choose among optional items.',
      choices: ['Accurate', correct('Inaccurate')],
     },	 
	 
    {questionHTML: 'For short-answer items, place blanks for incomplete statements near the beginning of the statement.',
      choices: ['Accurate', correct('Inaccurate')],
     },	 
   
	 
    {questionHTML: 'Insofar as possible, classroom teachers should evaluate their students’ essay responses anonymously, that is, without knowing which student wrote which response.',
     choices: [
       correct('Accurate'), 'Inaccurate',
               ],
     },	 
   
	 
    {questionHTML: 'Which of the following demonstrates the relationships between key curricular aims, student status inferences, and student responses to performance assessment tasks?',
     choices: [
       'Student responses to performance assessment tasks are derived from student status inferences, which are evidence for key curricular aims.',
       'Key curricular aims are derived from student status inferences, which are evidence for student response to performance assessment tasks.',
       'Student responses to performance assessment tasks are derived from key curricular aims, which are evidence for student status inferences.',
       correct('None-of-the-above.')
               ],
     },	 
   
	 
    {questionHTML: 'Which of the following is the primary issue with performance assessments in most settings?',
     choices: [
       'Choosing which curricular aim is the best one to assess using a performance assessment.',
       correct('The ability to generalize accurately about what skills and knowledge are possessed by the student.'),
       'Finding someone to assist in the scoring of the performance assessment.',
       'None-of-the-above.'
               ],
     },	 
   
	 
    {questionHTML: 'Which of the following is an important feature of the scoring rubric?',
     choices: [
       'The objectives to be analyzed.',
       correct('Descriptions of the evaluative criteria.'),
       'The numerical value of each item.',
       'The curricular aim to be assessed using the rubric.',

               ],
     },	 
   
	 
    {questionHTML: 'Which of the following is a source of error in scoring student performance?',
     choices: [
       'Bias coming from the test items.',
     'Unintentional cues in test items.',
     correct('Bias coming from the teacher.'),
     'Scantron machines.'
               ],
     },	 
   
	 
    {questionHTML: 'When held, portfolio conferences should not only deal with the evaluation of a student’s work products, but should also improve the student’s self-evaluation abilities.',
     choices: [
       correct('True'), 'False'
               ],
     },	 
   
	 
    {questionHTML: 'Students should be asked to review their own work products only near the end of the school year so their self-evaluations can be more accurate.',
     choices: [
       'True', correct('False')
               ],
     },	 
   
	 
    {questionHTML: 'Because students’ parents can ordinarily become heavily involved in portfolio assessment, a teacher’s first task is to make sure parents “own” their child’s portfolio.',
     choices: [
       'True', correct('False')
               ],
     },	 
   
  ],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Practices', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}

