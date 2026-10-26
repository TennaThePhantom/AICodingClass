import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import Database from "better-sqlite3";
import { z } from "zod";
import path from "path";

const DB_PATH = path.resolve("C:/task-manager/tasks.db");

const server = new McpServer({
	name: "task-db-server",
	version: "1.0.0",
});

server.tool(
	"tasks_by_status",
	"Returns all tasks whose status matches the given value.",
	{
		status: z
			.enum(["open", "in_progress", "completed"])
			.describe("Filter tasks by this status value"),
	},
	async ({ status }) => {
		const db = new Database(DB_PATH, { readonly: true });
		try {
			const rows = db
				.prepare(
					"SELECT id, title, assigned_to, due_date FROM tasks WHERE status = ? ORDER BY id",
				)
				.all(status);
			db.close();

			if (rows.length === 0) {
				return {
					content: [
						{ type: "text", text: `No tasks found for status: ${status}` },
					],
				};
			}

			const header =
				"ID | Title | Assigned To | Due Date\n" +
				"---+--------------------+-------------+-----------";
			const lines = rows.map(
				(r) =>
					`${r.id} | ${r.title} | ${r.assigned_to ?? ""} | ${r.due_date ?? ""}`,
			);
			return {
				content: [{ type: "text", text: [header, ...lines].join("\n") }],
			};
		} catch (err) {
			try {
				db.close();
			} catch {}
			return {
				content: [{ type: "text", text: `Error: ${err.message}` }],
				isError: true,
			};
		}
	},
);

server.tool(
	"update_task_status",
	"Updates the status column of a single task identified by its numeric id.",
	{
		id: z.number().int().positive().describe("Task ID to update"),
		status: z
			.enum(["open", "in_progress", "completed"])
			.describe("New status value"),
	},
	async ({ id, status }) => {
		const db = new Database(DB_PATH);
		try {
			const info = db
				.prepare("UPDATE tasks SET status = ? WHERE id = ?")
				.run(status, id);
			db.close();

			if (info.changes === 0) {
				return {
					content: [{ type: "text", text: `Task ${id}: not found` }],
				};
			}
			return {
				content: [
					{ type: "text", text: `Task ${id} updated to status: ${status}` },
				],
			};
		} catch (err) {
			try {
				db.close();
			} catch {}
			return {
				content: [{ type: "text", text: `Error: ${err.message}` }],
				isError: true,
			};
		}
	},
);

const transport = new StdioServerTransport();
await server.connect(transport);
