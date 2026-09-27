<?php

namespace Tests\Feature;

// use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ExampleTest extends TestCase
{
    /**
     * A basic test example.
     */
    public function test_the_homepage_redirects_to_embedding(): void
    {
        $response = $this->get('/');

        $response->assertRedirect(route('embedding.index'));
    }

    public function test_workflow_pages_render(): void
    {
        $this->get('/embedding')->assertOk();
        $this->get('/attack')->assertOk();
        $this->get('/extraction')->assertOk();
        $this->get('/evaluation')->assertOk();
    }
}
