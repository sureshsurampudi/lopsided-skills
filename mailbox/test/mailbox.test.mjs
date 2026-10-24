// Behavioral tests for mailbox unit-001, mapped to .todo/specs/mailbox-service.feature
// scenarios 1–2 (register creates expectation before exposure; re-registration
// rejected) and the pending discoverability claims.

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const CLI = new URL("../mailbox.mjs", import.meta.url).pathname;

function run(dir, ...args) {
  return execFileSync(process.execPath, [CLI, ...args], {
    env: { ...process.env, MAILBOX_DIR: dir },
    encoding: "utf8",
  });
}

function runExpectFailure(dir, ...args) {
  try {
    run(dir, ...args);
    assert.fail(`expected non-zero exit for: ${args.join(" ")}`);
  } catch (err) {
    assert.ok(err.status > 0, `non-zero exit expected, got ${err.status}`);
    return err;
  }
}

function makeDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "mailbox-test-"));
}

test("scenario 1: register creates a reply expectation before exposure", () => {
  const dir = makeDir();
  const out = run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "do the thing");
  assert.match(out, /registered r1 \(pending\)/);

  // discoverable as pending, no outcome
  const list = run(dir, "list", "--pending");
  assert.match(list, /^r1\t/);
  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.state, "pending");
  assert.equal(record.reply, null);
  assert.equal(record.delivered, false);
  assert.equal(record.requester, "q1");
  assert.equal(record.worker, "w1");
  assert.equal(record.instruction, "do the thing");
});

test("scenario 2: re-registration with a live expectation is rejected, original unchanged", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "first instruction");

  const err = runExpectFailure(dir, "register", "--id", "r1", "--requester", "q2", "--worker", "w2", "--instruction", "second instruction");
  assert.match(err.stderr, /already has a live expectation/);

  // original unchanged — no silent overwrite
  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.instruction, "first instruction");
  assert.equal(record.requester, "q1");
});

test("scenario 3: reply is persisted against the original request", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  run(dir, "dispatch", "--id", "r1");
  const out = run(dir, "reply", "--id", "r1", "--worker", "w1", "--status", "DONE", "--report", "all done");
  assert.match(out, /reply recorded for r1 \(DONE\)/);

  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.reply.status, "DONE");
  assert.equal(record.reply.report, "all done");
  assert.equal(record.reply.worker, "w1");
  assert.ok(record.reply.submittedAt);
  // no longer pending
  assert.equal(run(dir, "list", "--pending"), "");
});

test("scenario 4: duplicate reply keeps the first — one logical delivery", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  run(dir, "dispatch", "--id", "r1");
  run(dir, "reply", "--id", "r1", "--worker", "w1", "--status", "DONE", "--report", "first");
  const out = run(dir, "reply", "--id", "r1", "--worker", "w1", "--status", "FAILED", "--report", "second");
  assert.match(out, /ignored: first reply \(DONE\) already persisted/);

  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.reply.status, "DONE");
  assert.equal(record.reply.report, "first");
});

test("scenario 5: replaced worker identity cannot bind a reply; attempt stays inspectable", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  run(dir, "dispatch", "--id", "r1");
  const err = runExpectFailure(dir, "reply", "--id", "r1", "--worker", "w2", "--status", "DONE", "--report", "from impostor");
  assert.match(err.stderr, /does not match the dispatched worker identity "w1"/);

  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  // no outcome bound to the new session; rejected reply inspectable
  assert.equal(record.reply, null);
  assert.equal(record.rejectedReplies.length, 1);
  assert.equal(record.rejectedReplies[0].worker, "w2");
  assert.equal(record.rejectedReplies[0].status, "DONE");
  assert.equal(record.rejectedReplies[0].report, "from impostor");
  assert.ok(record.rejectedReplies[0].rejectedAt);
});

test("non-vocabulary status is rejected", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  run(dir, "dispatch", "--id", "r1");
  for (const status of ["PENDING", "done", "OK"]) {
    const err = runExpectFailure(dir, "reply", "--id", "r1", "--worker", "w1", "--status", status);
    assert.match(err.stderr, /outside the vocabulary/);
  }
  // nothing bound
  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.reply, null);
});

test("reply to an unknown requestId is not correlated (original requestId only)", () => {
  const dir = makeDir();
  const err = runExpectFailure(dir, "reply", "--id", "ghost", "--worker", "w1", "--status", "DONE");
  assert.match(err.stderr, /no request "ghost"/);
});

test("dispatch marks the request dispatched; it remains discoverable as pending until a reply", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  run(dir, "dispatch", "--id", "r1");
  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.state, "dispatched");
  assert.ok(record.dispatchedAt);
  // no reply bound → still pending per the feature file
  const list = run(dir, "list", "--pending");
  assert.match(list, /^r1\t/);
});

test("dispatch of an unknown request fails with not-found", () => {
  const dir = makeDir();
  const err = runExpectFailure(dir, "dispatch", "--id", "missing");
  assert.match(err.stderr, /no request "missing"/);
});

test("store persists across CLI invocations (same store, fresh process)", () => {
  const dir = makeDir();
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  // fresh process reads the same on-disk store
  const record = JSON.parse(run(dir, "show", "--id", "r1"));
  assert.equal(record.requestId, "r1");
});

test("list is empty before any registration and filters by pending", () => {
  const dir = makeDir();
  assert.equal(run(dir, "list"), "");
  assert.equal(run(dir, "list", "--pending"), "");
  run(dir, "register", "--id", "r1", "--requester", "q1", "--worker", "w1", "--instruction", "i");
  assert.equal(run(dir, "list").split("\n").filter(Boolean).length, 1);
});
