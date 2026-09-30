export default async function run(page, ui) {
  const email = `qa_${Date.now()}@example.com`;
  await page.goto('http://127.0.0.1:5173/register');
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByRole('textbox', { name: 'Full Name' }).fill('Browser QA User');
  await page.getByRole('textbox', { name: 'Password' }).fill('StrongPass123!');
  await page.getByRole('button', { name: 'Register' }).click();
  await page.waitForURL('**/jobs', { timeout: 30000 });
  await page.getByRole('heading', { name: 'Jobs' }).first().waitFor();
  const jobsText = await page.locator('body').innerText();
  await page.goto('http://127.0.0.1:5173/career-brain');
  await page.getByRole('heading', { name: 'Career Brain' }).first().waitFor();
  const brainText = await page.locator('body').innerText();
  await page.goto('http://127.0.0.1:5173/crm');
  await page.getByRole('heading', { name: 'CRM Workspace' }).first().waitFor();
  const crmText = await page.locator('body').innerText();
  await page.goto('http://127.0.0.1:5173/settings');
  await page.getByRole('heading', { name: 'Settings' }).first().waitFor();
  const settingsText = await page.locator('body').innerText();
  return {
    registeredEmail: email,
    finalPath: new URL(page.url()).pathname,
    jobsRendered: jobsText.includes('Jobs'),
    careerBrainRendered: brainText.includes('Career Brain'),
    crmRendered: crmText.includes('CRM Workspace'),
    settingsRendered: settingsText.includes('Settings'),
    snapshot: await ui.snapshot({ full: true })
  };
}
