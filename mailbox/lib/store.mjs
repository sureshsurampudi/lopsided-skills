// Persistent store for the mailbox service (issue #41).
//
// One JSON file per request under the store directory. Same host, same OS
// user: the default location is $MAILBOX_DIR or ~/.local/share/mailbox.
// Writes are atomic (tmp file + rename) so a crash never leaves a torn file.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export class StoreError extends Error {
  constructor(message, { exit = 2 } = {}) {
    super(message);
    this.exit = exit;
  }
}

export function storeDir() {
  return process.env.MAILBOX_DIR || path.join(os.homedir(), ".local", "share", "mailbox");
}

function recordPath(dir, requestId) {
  if (!/^[A-Za-z0-9._-]+$/.test(requestId)) {
    throw new StoreError(`invalid requestId: ${JSON.stringify(requestId)}`);
  }
  return path.join(dir, `${requestId}.json`);
}

export { recordPath };

const LOCK_POLL_MS = 25;
const LOCK_WAIT_MS = 5000;
const LOCK_STALE_MS = 10000; // operations are ms-scale; a holder that lives
// longer than this (crash) lets the next contender steal the lock.

// Serialize a per-request read-modify-write (R2.F1): the lock file is created
// exclusively (open wx), retried with backoff, stolen when stale, and always
// released in finally — including when the body exits via a thrown error.
export async function withLock(dir, requestId, body) {
  const lockPath = `${recordPath(dir, requestId)}.lock`;
  await fs.promises.mkdir(dir, { recursive: true });
  const deadline = Date.now() + LOCK_WAIT_MS;
  for (;;) {
    let handle;
    try {
      handle = await fs.promises.open(lockPath, "wx");
    } catch (err) {
      if (err.code !== "EEXIST") {
        throw new StoreError(`cannot lock request "${requestId}": ${err.message}`, { exit: 3 });
      }
      try {
        const st = await fs.promises.stat(lockPath);
        if (Date.now() - st.mtimeMs > LOCK_STALE_MS) {
          await fs.promises.rm(lockPath).catch(() => {});
          continue;
        }
      } catch { /* lock vanished between EEXIST and stat — retry */ }
      if (Date.now() > deadline) {
        throw new StoreError(`request "${requestId}" is busy (lock held); retry later`, { exit: 3 });
      }
      await new Promise((r) => setTimeout(r, LOCK_POLL_MS));
      continue;
    }
    try {
      return await body();
    } finally {
      await handle.close().catch(() => {});
      await fs.promises.rm(lockPath).catch(() => {});
    }
  }
}

export async function load(dir, requestId) {
  let raw;
  try {
    raw = await fs.promises.readFile(recordPath(dir, requestId), "utf8");
  } catch (err) {
    if (err.code === "ENOENT") return null;
    // Non-parse read failures (EISDIR from a directory at the record path,
    // EACCES, …) are rejected-class store failures (R2.F2): a clean one-line
    // message within the exit vocabulary, never a raw stack.
    throw new StoreError(`cannot read record "${requestId}": ${err.message}`, { exit: 3 });
  }
  try {
    return JSON.parse(raw);
  } catch {
    // A specifically addressed corrupt record is a rejected-class failure
    // (R1.F3): report cleanly within the exit vocabulary, never a raw stack.
    throw new StoreError(`record "${requestId}" is corrupt (unparseable store file)`, { exit: 3 });
  }
}

export async function save(dir, record) {
  await fs.promises.mkdir(dir, { recursive: true });
  const target = recordPath(dir, record.requestId);
  const tmp = `${target}.tmp.${process.pid}.${Date.now()}`;
  const data = JSON.stringify(record, null, 2) + "\n";
  const fh = await fs.promises.open(tmp, "w");
  try {
    await fh.writeFile(data);
    await fh.sync();
  } finally {
    await fh.close();
  }
  // Test-only hook (R2.F3 regression): simulate a crash after the tmp write
  // but before the rename — the window between the requester's acknowledgment
  // and the delivered mark. Inert without the env var.
  if (process.env.MAILBOX_FAIL_SAVE === "1") {
    await fs.promises.rm(tmp, { force: true });
    throw new StoreError("simulated save failure (MAILBOX_FAIL_SAVE)", { exit: 3 });
  }
  await fs.promises.rename(tmp, target);
}

export async function exists(dir, requestId) {
  try {
    await fs.promises.access(recordPath(dir, requestId));
    return true;
  } catch {
    return false;
  }
}

export async function list(dir, { pendingOnly = false } = {}) {
  let names;
  try {
    names = await fs.promises.readdir(dir);
  } catch (err) {
    if (err.code === "ENOENT") return [];
    // Directory-level enumeration failures (EACCES on the store dir, …) are
    // rejected-class store failures (R3.F3): a clean one-line message within
    // the exit vocabulary, never a raw stack — decision 012 holds here too.
    throw new StoreError(`cannot read store directory: ${err.message}`, { exit: 3 });
  }
  const records = [];
  const damaged = [];
  for (const name of names) {
    if (!name.endsWith(".json")) continue;
    let record;
    try {
      record = JSON.parse(await fs.promises.readFile(path.join(dir, name), "utf8"));
    } catch {
      // A damaged or unreadable file must not wedge pending discovery
      // (R1.F3/R2.F2): skip it with a warning; the exit code stays within
      // the documented vocabulary.
      damaged.push(name);
      continue;
    }
    if (pendingOnly && !isPending(record)) continue;
    records.push(record);
  }
  if (damaged.length) {
    console.error(`mailbox: warning: skipping unparseable store file(s): ${damaged.join(", ")}`);
  }
  records.sort((a, b) => a.requestId.localeCompare(b.requestId));
  return records;
}

// Pending = a live reply expectation: registered (dispatched or not), no
// reply bound, and not cancelled. Matches the feature file's "discoverable
// as pending".
export function isPending(record) {
  return (record.reply === null || record.reply === undefined) && record.state !== "cancelled";
}
