#pragma once

#include <cstdint>



extern "C" {
#if defined(_WIN32)
__declspec(dllexport)
#endif
std::uint8_t initializeReinterop(std::uint64_t validationHashValue, void** functionPointers, std::int32_t count);
}

