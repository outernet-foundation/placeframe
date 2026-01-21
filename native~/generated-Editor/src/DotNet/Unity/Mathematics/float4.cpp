#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float4;
}

namespace DotNet::Unity::Mathematics {

void (*float4::Construct_HRdOMAw1wcknBRlYiWJ61Q)(float x, float y, float z, float w, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) = nullptr;


float4 float4::Construct(float x, float y, float z, float w)
{
    void* reinteropException = nullptr;
    float4 result;
    Construct_HRdOMAw1wcknBRlYiWJ61Q(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


float (*DotNet::Unity::Mathematics::float4::Property_get_Item)(const ::DotNet::Unity::Mathematics::float4* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


float float4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


