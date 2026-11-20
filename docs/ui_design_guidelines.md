# UI Design Guidelines – Project 3 Absence & Capacity

One look and one way of working for every screen (Team, Employee, Login, …).
Examples to copy: the Team Management pages in `frontend/src/pages/`.

---

## 1. Tech and folders

- React + TypeScript + Vite. Page addresses with `react-router-dom`. Plain CSS in `frontend/src/style.css`.
- No new UI library without a team decision.

| Put | In |
|---|---|
| API calls and types for your feature | `src/api/<feature>.ts` (e.g. `employees.ts`) |
| One file per screen | `src/pages/<Name>Page.tsx` (e.g. `EmployeeListPage.tsx`) |
| Parts used by more than one screen | `src/components/` |
| Your routes | `src/App.tsx` – add your own `<Route>` lines only |

## 2. Page addresses

| Screen | Address |
|---|---|
| List | `/<things>` – e.g. `/teams`, `/employees` |
| Create | `/<things>/new` |
| Details | `/<things>/:id` |
| Edit | `/<things>/:id/edit` |

Lowercase, plural, English.

## 3. Page layout

Every page is one `<section>` inside the shared container:

```tsx
<section>
  <Link to="/teams" className="back">← Back to teams</Link>     {/* not on list pages */}
  <div className="page-head">
    <h2>Teams</h2>
    <button className="primary">+ Create team</button>          {/* main action, right */}
  </div>
  {/* messages, then content */}
</section>
```

- `h1` = app title only (in `App.tsx`). `h2` = page title. `h3` = section inside a page (e.g. "Members").
- Main action top right. Only **one** `primary` button per screen.

## 4. Colours

Use these, no other colours.

| Use | Colour |
|---|---|
| Text | `#172033` |
| Secondary text, hints, table headers | `#596579` |
| Page background | `#f5f7fb` |
| Cards, inputs | `white` |
| Borders | `#e5eaf2` (lines), `#c9d2e3` (inputs, buttons) |
| Primary (main button, links) | `#3451b2` |
| Success | text `#236b38` on `#eef8f0` |
| Error | text `#a5281b` on `#fdecea`; field error text `#c0392b` |
| Warning / info | text `#7a5a00` on `#fff6e0` |

## 5. Ready-made CSS classes

Use these classes instead of writing new styles.

| Need | Class |
|---|---|
| Main button | `<button className="primary">` |
| Normal button | `<button>` |
| Text-style button | `<button className="link">` |
| Link that looks like a button | `<Link className="button">` |
| Back link | `<Link className="back">← Back to …</Link>` |
| Table | `<table className="data-table">` – numbers: `className="num"` (right-aligned) |
| Status badge | `badge` (green, ACTIVE) · `badge badge-inactive` (grey) · `badge badge-lead` (blue) |
| Form field | `<div className="field">` with `label`, input, `hint`, `field-error` |
| Success message | `<p className="success" role="status">` |
| Error message | `<p className="form-error" role="alert">` |
| Info / not allowed | `<p className="notice">` |
| Empty list | `<p className="empty">` |
| Key–value details | `<dl className="team-card">` |
| Search box | `<input type="search" className="search">` |

New class needed? Add it to `style.css` in a block with your feature name as a comment.

## 6. Every page that loads data shows 4 states

| State | Show |
|---|---|
| Loading | `<p className="hint" role="status">Loading teams…</p>` |
| Error | the error message + **Retry** button (`className="form-error"`) |
| Empty | `<p className="empty">No teams yet.</p>` |
| Not found (details) | "Team not found" + back link |

No blank pages, no crashes.

## 7. Forms

- Field label with `*` when required: `Team name *`.
- Check in the browser **the same rules as the backend**, show the message **under the field**.
- Server errors: field errors under the field, others above the form (`form-error`).
- Buttons: **Save** (primary) then **Cancel**. While saving: Save disabled, text "Saving…".
- After saving: go to the list or details page and show a success message.
- Copy the pattern from `src/components/TeamForm.tsx`.

## 8. Talking to the backend

- Always use `apiRequest` from `src/api/client.ts`. Never call `fetch` yourself – it adds the login headers and
  turns errors into `ApiError`.
- Field names in TypeScript types = API names (camelCase).
- Decide by `error.code`, never by the message text:

```ts
catch (err) {
  if (err instanceof ApiError && err.code === "NOT_FOUND") { /* show "not found" */ }
  else setError(err instanceof ApiError ? err.message : "Something went wrong.");
}
```

## 9. Roles

- Show only the actions the current user may use (hide the button).
- The backend still checks every request – hiding is not security.
- The current user comes from `App.tsx` (`user.role`, `user.employeeId`); today the Demo login bar, later Member 4's
  login.
- Someone opens an address they may not use → show "Not allowed" (`notice`), not an empty form.

## 10. Texts

- English, short, sentence case: "Create team", not "CREATE TEAM" or "Create Team".
- Buttons are verbs: Save, Cancel, Edit, Deactivate.
- Messages say what happened: "Team “Development” was created."
- Ask before changes that are hard to undo: `window.confirm("Deactivate team “Development”?")`.
- Show dates as `DD.MM.YYYY`; the API uses `YYYY-MM-DD`.
- FTE as a number with "FTE": `5 FTE`, `0.8`.

## 11. Accessibility and small screens

- Every input has a `<label htmlFor>`; buttons have text.
- Messages use `role="status"` (success, loading) or `role="alert"` (errors).
- Works at phone width: no fixed widths. Wrap wide tables in `<div className="table-scroll">` so they scroll sideways.

## 12. Before your pull request

- [ ] Uses the classes and colours above, no new colours
- [ ] Loading, error, empty (and not-found) states shown
- [ ] Form checks match the backend; server errors shown on the form
- [ ] Actions hidden for roles that may not use them
- [ ] API calls only through `src/api/`
- [ ] Your routes follow section 2
- [ ] `npm run build` passes
