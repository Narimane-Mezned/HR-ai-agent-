/**
 * @typedef {Object} Job
 * @property {number} id
 * @property {string} title
 * @property {string} description
 * @property {string} requirements
 * @property {string} created_by
 * @property {string} created_at
 */

/**
 * @typedef {Object} Candidate
 * @property {number} id
 * @property {string} name
 * @property {number} cv_length
 */

/**
 * @typedef {Object} Screening
 * @property {number} candidate_id
 * @property {string} candidate_name
 * @property {number|null} score
 * @property {string} verdict
 * @property {string} justification
 * @property {string} category
 */

/**
 * @typedef {Object} Interview
 * @property {string} candidate_name
 * @property {string} job_title
 * @property {string} confirmed_time
 */

export {};
