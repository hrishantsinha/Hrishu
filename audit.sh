echo "=== FILES ==="
ls -la *.py
echo ""
echo "=== LINE COUNTS ==="
wc -l *.py
echo ""
echo "=== COMMANDS REGISTERED IN bot.py ==="
grep -n "CommandHandler(" bot.py
echo ""
echo "=== FUNCTIONS IN pokemon_commands.py ==="
grep -n "^async def" pokemon_commands.py
echo ""
echo "=== FUNCTIONS IN database.py ==="
grep -n "^def " database.py
echo ""
echo "=== spawn_wild SEARCH (ALL FILES) ==="
grep -rn "spawn_wild" *.py
echo ""
echo "=== RUNNING PYTHON PROCESSES ==="
ps aux | grep python
