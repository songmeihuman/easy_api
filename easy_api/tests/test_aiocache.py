from aiocache import cached


async def test_cached():
    call_count = 0

    @cached()
    async def mock_file(name):
        nonlocal call_count
        call_count += 1
        return f'hello {name}'

    content = await mock_file('tom')
    assert content == 'hello tom'
    assert call_count == 1

    content = await mock_file('tom')
    assert content == 'hello tom'
    assert call_count == 1

    content = await mock_file('jerry')
    assert content == 'hello jerry'
    assert call_count == 2
