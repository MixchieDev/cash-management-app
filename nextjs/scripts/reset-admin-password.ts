/**
 * Reset the admin user's password in Convex.
 * Usage: npx tsx scripts/reset-admin-password.ts <new-password>
 */
import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";
import { hash } from "bcryptjs";
import * as dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

const CONVEX_URL = process.env.NEXT_PUBLIC_CONVEX_URL!;
const convex = new ConvexHttpClient(CONVEX_URL);

async function main() {
  const newPassword = process.argv[2];
  if (!newPassword) {
    console.error("Usage: npx tsx scripts/reset-admin-password.ts <new-password>");
    process.exit(1);
  }

  // Find admin user
  const user = await convex.query(api.users.getByUsername, { username: "admin" });
  if (!user) {
    console.error("No 'admin' user found. Creating one...");
    const passwordHash = await hash(newPassword, 10);
    await convex.mutation(api.users.create as any, {
      username: "admin",
      passwordHash,
      name: "Admin",
      role: "admin",
      permissions: [
        "view_dashboard", "view_contracts", "edit_contracts",
        "view_scenarios", "edit_scenarios", "manage_overrides",
        "import_data", "manage_settings", "delete_data", "manage_users",
      ],
    });
    console.log("✅ Created admin user with the provided password.");
    return;
  }

  // Reset password
  const passwordHash = await hash(newPassword, 10);
  await convex.mutation(api.users.updatePassword as any, {
    id: user._id,
    passwordHash,
  });

  console.log(`✅ Password reset for user 'admin' (${user.name})`);
}

main().catch(console.error);
