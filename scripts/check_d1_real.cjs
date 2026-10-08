/* Real local workflow. Users enter credentials privately; no traces or auth dumps. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path = require('node:path');
let stage = 'startup';
(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome', args: ['--start-maximized'] });
  const page = await browser.newPage({ viewport: null });
  page.setDefaultTimeout(90000);
  const privateLogin = async (role) => {
    console.log(`WAIT: private ${role} sign-in in the Chrome application window`);
    await page.getByRole('link', { name: role === 'administrator' ? 'Evidence & restrictions' : 'Teacher inbox', exact: true }).waitFor({ timeout: 900000 });
    console.log(`PASS: real ${role} sign-in`);
  };
  try {
    await page.goto('http://127.0.0.1:5173');
    await privateLogin('administrator');
    if (!process.env.AIRWISE_RESUME_CONFIRMED) {
    stage = 'evidence';
    await page.getByRole('link', { name: 'Evidence & restrictions', exact: true }).click();
    await page.getByRole('button', { name: 'Synthetic replay', exact: true }).click();
    await page.getByRole('button', { name: 'Use synthetic notice' }).click();
    await page.getByRole('button', { name: 'Interpret notice', exact: true }).click();
    await page.getByRole('checkbox', { name: 'Outdoor spaces unavailable', exact: true }).check();
    await page.getByLabel('Reviewed calendar date').fill('2026-10-12');
    await page.getByRole('checkbox', { name: 'Period 2', exact: true }).check();
    await page.getByLabel('Notice source and authenticity reviewed').check();
    await page.getByLabel('Dates, period scope and ambiguities reviewed').check();
    await page.getByRole('button', { name: 'Confirm reviewed restrictions' }).click();
    await page.getByText('Restrictions confirmed. The existing approved plan is retained', { exact: false }).waitFor();
    console.log('PASS: actual interpretation and administrator confirmation');
    }
    stage = 'approval';
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    await page.getByText('Loading...', { exact: true }).waitFor({ state: 'hidden' }).catch(() => {});
    await page.waitForTimeout(5000);
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByText('Draft generated; approval is still required.').waitFor();
    await page.getByRole('button', { name: 'Approve this version' }).click();
    await page.getByText('Approval recorded for this version.').waitFor();
    await page.screenshot({ path: path.join(__dirname, '../work/d1-real-approved.png'), fullPage: true });
    console.log('PASS: actual validated draft approval');
    await page.getByRole('button', { name: 'Sign out' }).click();
    await privateLogin('teacher');
    stage = 'teacher report';
    await page.getByRole('button', { name: 'Acknowledge this version' }).click();
    await page.getByRole('button', { name: 'Acknowledged', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COULD_NOT_IMPLEMENT');
    await page.getByLabel('Note (optional)').fill('SYNTHETIC BROWSER CHECK: classroom unavailable');
    await page.getByRole('button', { name: 'Save execution report' }).click();
    await page.locator('tr[data-activity="6-a:Mon-2"]').getByText('Could not implement', { exact: true }).waitFor();
    console.log('PASS: actual acknowledgement and execution exception');
    await page.reload();
    await page.getByRole('heading', { name: 'Teacher inbox', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Sign out' }).click();
    await privateLogin('administrator');
    stage = 'review';
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByText('SYNTHETIC BROWSER CHECK: classroom unavailable').first().waitFor();
    await page.screenshot({ path: path.join(__dirname, '../work/d1-real-review.png'), fullPage: true });
    console.log('PASS REAL: Cognito sign-in, interpretation, confirmation, validated approval, teacher acknowledgement/exception, reload and administrator review');
  } finally { await browser.close(); }
})().catch(error => { console.error(`FAIL real browser workflow: ${stage}, ${error.name}; credential/request contents withheld`); process.exitCode = 1; });
