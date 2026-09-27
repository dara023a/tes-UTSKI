<?php

declare(strict_types=1);

namespace App\Services;

use RuntimeException;

final class PythonEngineException extends RuntimeException
{
    public function __construct(
        string $message,
        public readonly string $errorType,
    ) {
        parent::__construct($message);
    }
}
