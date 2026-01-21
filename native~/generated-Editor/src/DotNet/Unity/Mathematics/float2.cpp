#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float2;
}

namespace DotNet::Unity::Mathematics {

void (*float2::Construct_aHAAcVLY3x5GFF0HQijktQ)(float x, float y, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) = nullptr;


float2 float2::Construct(float x, float y)
{
    void* reinteropException = nullptr;
    float2 result;
    Construct_aHAAcVLY3x5GFF0HQijktQ(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


float (*DotNet::Unity::Mathematics::float2::Property_get_Item)(const ::DotNet::Unity::Mathematics::float2* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


float float2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


